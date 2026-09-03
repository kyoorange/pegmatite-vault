import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import ResourceInUseError, ResourceNotFoundError
from app.models.locality import Locality
from app.models.specimen import Specimen
from app.schemas.locality import LocalityPage, LocalityResponse, LocalityWrite
from app.schemas.specimen import SpecimenPage
from app.services.specimens import list_specimens


def _specimen_count():
    return (
        select(func.count())
        .select_from(Specimen)
        .where(Specimen.locality_id == Locality.id)
        .correlate(Locality)
        .scalar_subquery()
    )


def _response(locality: Locality, specimen_count: int) -> LocalityResponse:
    return LocalityResponse(
        id=locality.id,
        locality_name=locality.locality_name,
        alias_name=locality.alias_name,
        latitude=locality.latitude,
        longitude=locality.longitude,
        note=locality.note,
        specimen_count=specimen_count,
    )


def list_localities(db: Session, *, page: int, page_size: int, q: str | None) -> LocalityPage:
    conditions = []
    if q:
        term = f"%{q.strip()}%"
        conditions.append(
            or_(
                Locality.locality_name.ilike(term),
                Locality.alias_name.ilike(term),
                Locality.note.ilike(term),
            )
        )
    total = db.scalar(select(func.count()).select_from(Locality).where(*conditions)) or 0
    statement = (
        select(Locality, _specimen_count())
        .where(*conditions)
        .order_by(Locality.locality_name, Locality.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return LocalityPage(
        items=[_response(locality, count) for locality, count in db.execute(statement)],
        page=page,
        page_size=page_size,
        total=total,
    )


def get_locality(db: Session, locality_id: uuid.UUID) -> LocalityResponse:
    row = db.execute(
        select(Locality, _specimen_count()).where(Locality.id == locality_id)
    ).one_or_none()
    if row is None:
        raise ResourceNotFoundError("locality", locality_id)
    return _response(row[0], row[1])


def list_related_specimens(
    db: Session, locality_id: uuid.UUID, *, page: int, page_size: int
) -> SpecimenPage:
    if db.get(Locality, locality_id) is None:
        raise ResourceNotFoundError("locality", locality_id)
    return list_specimens(
        db,
        page=page,
        page_size=page_size,
        locality_id=locality_id,
    )


def create_locality(db: Session, payload: LocalityWrite) -> LocalityResponse:
    locality = Locality(**payload.model_dump())
    db.add(locality)
    db.commit()
    return get_locality(db, locality.id)


def update_locality(
    db: Session, locality_id: uuid.UUID, payload: LocalityWrite
) -> LocalityResponse:
    locality = db.get(Locality, locality_id)
    if locality is None:
        raise ResourceNotFoundError("locality", locality_id)
    for name, value in payload.model_dump().items():
        setattr(locality, name, value)
    db.commit()
    return get_locality(db, locality_id)


def delete_locality(db: Session, locality_id: uuid.UUID) -> None:
    locality = db.get(Locality, locality_id)
    if locality is None:
        raise ResourceNotFoundError("locality", locality_id)
    reference_count = (
        db.scalar(select(func.count()).where(Specimen.locality_id == locality_id)) or 0
    )
    if reference_count:
        raise ResourceInUseError("locality", locality_id, reference_count)
    db.delete(locality)
    db.commit()
