import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import InvalidReferenceError, ResourceInUseError, ResourceNotFoundError
from app.models.mineral import Mineral
from app.models.mineral_class import MineralClass
from app.models.specimen_mineral import specimen_minerals
from app.schemas.mineral import MineralClassSummary, MineralPage, MineralResponse, MineralWrite
from app.schemas.specimen import SpecimenPage
from app.services.specimens import list_specimens


def _specimen_count():
    return (
        select(func.count())
        .select_from(specimen_minerals)
        .where(specimen_minerals.c.mineral_id == Mineral.id)
        .correlate(Mineral)
        .scalar_subquery()
    )


def _response(mineral: Mineral, specimen_count: int) -> MineralResponse:
    return MineralResponse(
        id=mineral.id,
        japanese_name=mineral.japanese_name,
        english_name=mineral.english_name,
        formula=mineral.formula,
        crystal_system=mineral.crystal_system,
        mineral_class=(
            MineralClassSummary(
                id=mineral.mineral_class.id,
                name=mineral.mineral_class.name,
                description=mineral.mineral_class.description,
            )
            if mineral.mineral_class
            else None
        ),
        description=mineral.description,
        specimen_count=specimen_count,
    )


def list_minerals(
    db: Session,
    *,
    page: int,
    page_size: int,
    q: str | None,
    mineral_class_id: int | None,
    sort: str,
    order: str,
) -> MineralPage:
    count_column = _specimen_count().label("specimen_count")
    conditions = []
    if q:
        term = f"%{q.strip()}%"
        conditions.append(
            or_(
                Mineral.japanese_name.ilike(term),
                Mineral.english_name.ilike(term),
                Mineral.formula.ilike(term),
            )
        )
    if mineral_class_id is not None:
        conditions.append(Mineral.mineral_class_id == mineral_class_id)

    total = db.scalar(select(func.count()).select_from(Mineral).where(*conditions)) or 0
    sort_column = {
        "japanese_name": Mineral.japanese_name,
        "english_name": Mineral.english_name,
        "specimen_count": count_column,
    }[sort]
    ordering = sort_column.asc() if order == "asc" else sort_column.desc()
    statement = (
        select(Mineral, count_column)
        .options(selectinload(Mineral.mineral_class))
        .where(*conditions)
        .order_by(ordering, Mineral.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return MineralPage(
        items=[_response(mineral, count) for mineral, count in db.execute(statement)],
        page=page,
        page_size=page_size,
        total=total,
    )


def get_mineral(db: Session, mineral_id: uuid.UUID) -> MineralResponse:
    statement = (
        select(Mineral, _specimen_count())
        .options(selectinload(Mineral.mineral_class))
        .where(Mineral.id == mineral_id)
    )
    row = db.execute(statement).one_or_none()
    if row is None:
        raise ResourceNotFoundError("mineral", mineral_id)
    return _response(row[0], row[1])


def list_related_specimens(
    db: Session, mineral_id: uuid.UUID, *, page: int, page_size: int
) -> SpecimenPage:
    if db.get(Mineral, mineral_id) is None:
        raise ResourceNotFoundError("mineral", mineral_id)
    return list_specimens(
        db,
        page=page,
        page_size=page_size,
        mineral_id=mineral_id,
    )


def _validate_class(db: Session, mineral_class_id: int | None) -> None:
    if mineral_class_id is not None and db.get(MineralClass, mineral_class_id) is None:
        raise InvalidReferenceError("mineral_class", [mineral_class_id])


def create_mineral(db: Session, payload: MineralWrite) -> MineralResponse:
    _validate_class(db, payload.mineral_class_id)
    mineral = Mineral(**payload.model_dump())
    db.add(mineral)
    db.commit()
    return get_mineral(db, mineral.id)


def update_mineral(db: Session, mineral_id: uuid.UUID, payload: MineralWrite) -> MineralResponse:
    mineral = db.get(Mineral, mineral_id)
    if mineral is None:
        raise ResourceNotFoundError("mineral", mineral_id)
    _validate_class(db, payload.mineral_class_id)
    for name, value in payload.model_dump().items():
        setattr(mineral, name, value)
    db.commit()
    return get_mineral(db, mineral_id)


def delete_mineral(db: Session, mineral_id: uuid.UUID) -> None:
    mineral = db.get(Mineral, mineral_id)
    if mineral is None:
        raise ResourceNotFoundError("mineral", mineral_id)
    reference_count = db.scalar(
        select(func.count())
        .select_from(specimen_minerals)
        .where(specimen_minerals.c.mineral_id == mineral_id)
    )
    if reference_count:
        raise ResourceInUseError("mineral", mineral_id, reference_count)
    db.delete(mineral)
    db.commit()
