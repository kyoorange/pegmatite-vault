import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.locality import LocalityPage, LocalityResponse, LocalityWrite
from app.schemas.specimen import SpecimenPage
from app.services import localities as service

router = APIRouter(prefix="/localities", tags=["Localities"])
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=LocalityPage, operation_id="listLocalities")
def list_localities(
    db: DatabaseSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 24,
    q: str | None = None,
) -> LocalityPage:
    return service.list_localities(db, page=page, page_size=page_size, q=q)


@router.post(
    "",
    response_model=LocalityResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="createLocality",
)
def create_locality(payload: LocalityWrite, db: DatabaseSession) -> LocalityResponse:
    return service.create_locality(db, payload)


@router.get("/{locality_id}", response_model=LocalityResponse, operation_id="getLocality")
def get_locality(locality_id: uuid.UUID, db: DatabaseSession) -> LocalityResponse:
    return service.get_locality(db, locality_id)


@router.put("/{locality_id}", response_model=LocalityResponse, operation_id="updateLocality")
def update_locality(
    locality_id: uuid.UUID, payload: LocalityWrite, db: DatabaseSession
) -> LocalityResponse:
    return service.update_locality(db, locality_id, payload)


@router.delete(
    "/{locality_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="deleteLocality",
)
def delete_locality(locality_id: uuid.UUID, db: DatabaseSession) -> Response:
    service.delete_locality(db, locality_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{locality_id}/specimens",
    response_model=SpecimenPage,
    operation_id="listLocalitySpecimens",
)
def list_locality_specimens(
    locality_id: uuid.UUID,
    db: DatabaseSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 24,
) -> SpecimenPage:
    return service.list_related_specimens(db, locality_id, page=page, page_size=page_size)
