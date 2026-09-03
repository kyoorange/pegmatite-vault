import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import InvalidReferenceError, ResourceNotFoundError
from app.models.acquisition_method import AcquisitionMethod
from app.models.locality import Locality
from app.models.mineral import Mineral
from app.models.specimen import Specimen
from app.schemas.specimen import (
    AcquisitionMethodSummary,
    ImageSummary,
    LocalitySummary,
    MineralSummary,
    SpecimenCreate,
    SpecimenDetail,
    SpecimenPage,
    SpecimenSummary,
    SpecimenUpdate,
)


def _options() -> tuple:
    return (
        selectinload(Specimen.locality),
        selectinload(Specimen.acquisition_method),
        selectinload(Specimen.minerals),
        selectinload(Specimen.images),
    )


def _summary(specimen: Specimen) -> SpecimenSummary:
    active_images = sorted(
        (image for image in specimen.images if image.status == "active"),
        key=lambda image: image.sort_order,
    )
    return SpecimenSummary(
        id=specimen.id,
        specimen_no=specimen.specimen_no,
        specimen_name=specimen.specimen_name,
        locality=LocalitySummary.model_validate(specimen.locality) if specimen.locality else None,
        favorite=specimen.favorite,
        mineral_names=[mineral.japanese_name for mineral in specimen.minerals],
        thumbnail_image_id=active_images[0].id if active_images else None,
        created_at=specimen.created_at,
        updated_at=specimen.updated_at,
    )


def _detail(specimen: Specimen) -> SpecimenDetail:
    summary = _summary(specimen)
    active_images = sorted(
        (image for image in specimen.images if image.status == "active"),
        key=lambda image: image.sort_order,
    )
    return SpecimenDetail(
        **summary.model_dump(),
        acquisition_method=(
            AcquisitionMethodSummary.model_validate(specimen.acquisition_method)
            if specimen.acquisition_method
            else None
        ),
        collection_date=specimen.collection_date,
        features=specimen.features,
        note=specimen.note,
        minerals=[MineralSummary.model_validate(mineral) for mineral in specimen.minerals],
        images=[
            ImageSummary(
                id=image.id,
                specimen_id=image.specimen_id,
                original_filename=image.original_filename,
                media_type=image.media_type,
                file_size=image.file_size,
                caption=image.caption,
                sort_order=image.sort_order,
                status=image.status,
                archived_at=image.archived_at,
                created_at=image.created_at,
            )
            for image in active_images
        ],
    )


def _get_model(db: Session, specimen_id: uuid.UUID) -> Specimen:
    statement = select(Specimen).options(*_options()).where(Specimen.id == specimen_id)
    specimen = db.scalar(statement)
    if specimen is None:
        raise ResourceNotFoundError("specimen", specimen_id)
    return specimen


def _apply_filters(
    statement: Select,
    *,
    q: str | None,
    mineral_id: uuid.UUID | None,
    locality_id: uuid.UUID | None,
    acquisition_method_id: int | None,
    favorite: bool | None,
) -> Select:
    if q:
        term = f"%{q.strip()}%"
        number_term = int(q) if q.strip().isdigit() else None
        conditions = [
            Specimen.specimen_name.ilike(term),
            Specimen.locality.has(Locality.locality_name.ilike(term)),
            Specimen.minerals.any(Mineral.japanese_name.ilike(term)),
            Specimen.minerals.any(Mineral.english_name.ilike(term)),
        ]
        if number_term is not None:
            conditions.append(Specimen.specimen_no == number_term)
        statement = statement.where(or_(*conditions))
    if mineral_id:
        statement = statement.where(Specimen.minerals.any(Mineral.id == mineral_id))
    if locality_id:
        statement = statement.where(Specimen.locality_id == locality_id)
    if acquisition_method_id:
        statement = statement.where(Specimen.acquisition_method_id == acquisition_method_id)
    if favorite is not None:
        statement = statement.where(Specimen.favorite == favorite)
    return statement


def list_specimens(
    db: Session,
    *,
    page: int,
    page_size: int,
    q: str | None = None,
    mineral_id: uuid.UUID | None = None,
    locality_id: uuid.UUID | None = None,
    acquisition_method_id: int | None = None,
    favorite: bool | None = None,
    sort: str = "created_at",
    order: str = "desc",
) -> SpecimenPage:
    filtered = _apply_filters(
        select(Specimen),
        q=q,
        mineral_id=mineral_id,
        locality_id=locality_id,
        acquisition_method_id=acquisition_method_id,
        favorite=favorite,
    )
    total = db.scalar(select(func.count()).select_from(filtered.subquery())) or 0
    sort_column = {
        "created_at": Specimen.created_at,
        "specimen_no": Specimen.specimen_no,
        "specimen_name": Specimen.specimen_name,
    }[sort]
    ordering = sort_column.asc() if order == "asc" else sort_column.desc()
    statement = (
        filtered.options(*_options())
        .order_by(ordering, Specimen.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return SpecimenPage(
        items=[_summary(item) for item in db.scalars(statement).all()],
        page=page,
        page_size=page_size,
        total=total,
    )


def get_specimen(db: Session, specimen_id: uuid.UUID) -> SpecimenDetail:
    return _detail(_get_model(db, specimen_id))


def _validate_references(
    db: Session,
    locality_id: uuid.UUID | None,
    acquisition_method_id: int | None,
    mineral_ids: list[uuid.UUID],
) -> list[Mineral]:
    if locality_id is not None and db.get(Locality, locality_id) is None:
        raise InvalidReferenceError("locality", [locality_id])
    if (
        acquisition_method_id is not None
        and db.get(AcquisitionMethod, acquisition_method_id) is None
    ):
        raise InvalidReferenceError("acquisition_method", [acquisition_method_id])
    unique_ids = list(dict.fromkeys(mineral_ids))
    minerals = (
        list(db.scalars(select(Mineral).where(Mineral.id.in_(unique_ids)))) if unique_ids else []
    )
    found_ids = {mineral.id for mineral in minerals}
    missing = [mineral_id for mineral_id in unique_ids if mineral_id not in found_ids]
    if missing:
        raise InvalidReferenceError("mineral", missing)
    return minerals


def _next_specimen_no(db: Session, locality_id: uuid.UUID | None) -> int:
    statement = select(func.max(Specimen.specimen_no))
    statement = (
        statement.where(Specimen.locality_id == locality_id)
        if locality_id is not None
        else statement.where(Specimen.locality_id.is_(None))
    )
    return (db.scalar(statement) or 0) + 1


def create_specimen(db: Session, payload: SpecimenCreate) -> SpecimenDetail:
    minerals = _validate_references(
        db, payload.locality_id, payload.acquisition_method_id, payload.mineral_ids
    )
    values = payload.model_dump(exclude={"mineral_ids"})
    if values["specimen_no"] is None:
        values["specimen_no"] = _next_specimen_no(db, payload.locality_id)
    specimen = Specimen(**values, minerals=minerals)
    db.add(specimen)
    db.commit()
    return get_specimen(db, specimen.id)


def update_specimen(db: Session, specimen_id: uuid.UUID, payload: SpecimenUpdate) -> SpecimenDetail:
    specimen = _get_model(db, specimen_id)
    changes = payload.model_dump(exclude_unset=True)
    if "mineral_ids" in changes:
        mineral_ids = changes.pop("mineral_ids") or []
        specimen.minerals = _validate_references(
            db,
            changes.get("locality_id", specimen.locality_id),
            changes.get("acquisition_method_id", specimen.acquisition_method_id),
            mineral_ids,
        )
    else:
        _validate_references(
            db,
            changes.get("locality_id", specimen.locality_id),
            changes.get("acquisition_method_id", specimen.acquisition_method_id),
            [],
        )
    for name, value in changes.items():
        setattr(specimen, name, value)
    specimen.updated_at = datetime.now(UTC)
    db.commit()
    return get_specimen(db, specimen.id)


def delete_specimen(db: Session, specimen_id: uuid.UUID) -> None:
    specimen = _get_model(db, specimen_id)
    archived_at = datetime.now(UTC)
    for image in specimen.images:
        if image.status == "active":
            image.archived_from_specimen_id = specimen.id
            image.specimen = None
            image.status = "archived"
            image.archived_at = archived_at
    db.flush()
    db.delete(specimen)
    db.commit()
