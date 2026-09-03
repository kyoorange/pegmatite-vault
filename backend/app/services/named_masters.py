from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import (
    DuplicateResourceError,
    ResourceInUseError,
    ResourceNotFoundError,
)
from app.models.acquisition_method import AcquisitionMethod
from app.models.mineral import Mineral
from app.models.mineral_class import MineralClass
from app.models.specimen import Specimen
from app.schemas.named_master import NamedMasterResponse, NamedMasterWrite


def _model(resource: str):
    return MineralClass if resource == "mineral_class" else AcquisitionMethod


def list_items(db: Session, resource: str) -> list[NamedMasterResponse]:
    model = _model(resource)
    return [
        NamedMasterResponse.model_validate(item)
        for item in db.scalars(select(model).order_by(model.id))
    ]


def get_item(db: Session, resource: str, item_id: int) -> NamedMasterResponse:
    item = db.get(_model(resource), item_id)
    if item is None:
        raise ResourceNotFoundError(resource, item_id)
    return NamedMasterResponse.model_validate(item)


def _ensure_unique(db: Session, resource: str, name: str, exclude_id: int | None = None) -> None:
    model = _model(resource)
    statement = select(model.id).where(model.name == name)
    if exclude_id is not None:
        statement = statement.where(model.id != exclude_id)
    if db.scalar(statement) is not None:
        raise DuplicateResourceError(resource, "name")


def create_item(db: Session, resource: str, payload: NamedMasterWrite) -> NamedMasterResponse:
    _ensure_unique(db, resource, payload.name)
    item = _model(resource)(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return NamedMasterResponse.model_validate(item)


def update_item(
    db: Session, resource: str, item_id: int, payload: NamedMasterWrite
) -> NamedMasterResponse:
    item = db.get(_model(resource), item_id)
    if item is None:
        raise ResourceNotFoundError(resource, item_id)
    _ensure_unique(db, resource, payload.name, item_id)
    item.name = payload.name
    item.description = payload.description
    db.commit()
    db.refresh(item)
    return NamedMasterResponse.model_validate(item)


def delete_item(db: Session, resource: str, item_id: int) -> None:
    item = db.get(_model(resource), item_id)
    if item is None:
        raise ResourceNotFoundError(resource, item_id)
    reference_count = (
        db.scalar(
            select(func.count()).where(
                Mineral.mineral_class_id == item_id
                if resource == "mineral_class"
                else Specimen.acquisition_method_id == item_id
            )
        )
        or 0
    )
    if reference_count:
        raise ResourceInUseError(resource, item_id, reference_count)
    db.delete(item)
    db.commit()
