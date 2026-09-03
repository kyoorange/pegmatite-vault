import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.specimen import (
    SpecimenCreate,
    SpecimenDetail,
    SpecimenPage,
    SpecimenUpdate,
)
from app.services import specimens as service

router = APIRouter(prefix="/specimens", tags=["Specimens"])
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=SpecimenPage, operation_id="listSpecimens")
def list_specimens(
    db: DatabaseSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 24,
    q: str | None = None,
    mineral_id: uuid.UUID | None = None,
    locality_id: uuid.UUID | None = None,
    acquisition_method_id: Annotated[int | None, Query(ge=1)] = None,
    favorite: bool | None = None,
    sort: Literal["created_at", "specimen_no", "specimen_name"] = "created_at",
    order: Literal["asc", "desc"] = "desc",
) -> SpecimenPage:
    return service.list_specimens(
        db,
        page=page,
        page_size=page_size,
        q=q,
        mineral_id=mineral_id,
        locality_id=locality_id,
        acquisition_method_id=acquisition_method_id,
        favorite=favorite,
        sort=sort,
        order=order,
    )


@router.post(
    "",
    response_model=SpecimenDetail,
    status_code=status.HTTP_201_CREATED,
    operation_id="createSpecimen",
)
def create_specimen(payload: SpecimenCreate, db: DatabaseSession) -> SpecimenDetail:
    return service.create_specimen(db, payload)


@router.get("/{specimen_id}", response_model=SpecimenDetail, operation_id="getSpecimen")
def get_specimen(specimen_id: uuid.UUID, db: DatabaseSession) -> SpecimenDetail:
    return service.get_specimen(db, specimen_id)


@router.patch("/{specimen_id}", response_model=SpecimenDetail, operation_id="updateSpecimen")
def update_specimen(
    specimen_id: uuid.UUID, payload: SpecimenUpdate, db: DatabaseSession
) -> SpecimenDetail:
    return service.update_specimen(db, specimen_id, payload)


@router.delete(
    "/{specimen_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="deleteSpecimen",
)
def delete_specimen(specimen_id: uuid.UUID, db: DatabaseSession) -> Response:
    service.delete_specimen(db, specimen_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
