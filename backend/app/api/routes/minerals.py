import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.mineral import MineralPage, MineralResponse, MineralWrite
from app.schemas.specimen import SpecimenPage
from app.services import minerals as service

router = APIRouter(prefix="/minerals", tags=["Minerals"])
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=MineralPage, operation_id="listMinerals")
def list_minerals(
    db: DatabaseSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 24,
    q: str | None = None,
    mineral_class_id: Annotated[int | None, Query(ge=1)] = None,
    sort: Literal["japanese_name", "english_name", "specimen_count"] = "japanese_name",
    order: Literal["asc", "desc"] = "asc",
) -> MineralPage:
    return service.list_minerals(
        db,
        page=page,
        page_size=page_size,
        q=q,
        mineral_class_id=mineral_class_id,
        sort=sort,
        order=order,
    )


@router.post(
    "",
    response_model=MineralResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="createMineral",
)
def create_mineral(payload: MineralWrite, db: DatabaseSession) -> MineralResponse:
    return service.create_mineral(db, payload)


@router.get("/{mineral_id}", response_model=MineralResponse, operation_id="getMineral")
def get_mineral(mineral_id: uuid.UUID, db: DatabaseSession) -> MineralResponse:
    return service.get_mineral(db, mineral_id)


@router.put("/{mineral_id}", response_model=MineralResponse, operation_id="updateMineral")
def update_mineral(
    mineral_id: uuid.UUID, payload: MineralWrite, db: DatabaseSession
) -> MineralResponse:
    return service.update_mineral(db, mineral_id, payload)


@router.delete(
    "/{mineral_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="deleteMineral",
)
def delete_mineral(mineral_id: uuid.UUID, db: DatabaseSession) -> Response:
    service.delete_mineral(db, mineral_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{mineral_id}/specimens",
    response_model=SpecimenPage,
    operation_id="listMineralSpecimens",
)
def list_mineral_specimens(
    mineral_id: uuid.UUID,
    db: DatabaseSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 24,
) -> SpecimenPage:
    return service.list_related_specimens(db, mineral_id, page=page, page_size=page_size)
