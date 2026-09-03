from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.named_master import NamedMasterResponse, NamedMasterWrite
from app.services import named_masters as service

router = APIRouter(tags=["Masters"])
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get(
    "/mineral-classes",
    response_model=list[NamedMasterResponse],
    operation_id="listMineralClasses",
)
def list_mineral_classes(db: DatabaseSession) -> list[NamedMasterResponse]:
    return service.list_items(db, "mineral_class")


@router.post(
    "/mineral-classes",
    response_model=NamedMasterResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="createMineralClass",
)
def create_mineral_class(payload: NamedMasterWrite, db: DatabaseSession) -> NamedMasterResponse:
    return service.create_item(db, "mineral_class", payload)


@router.get(
    "/mineral-classes/{mineral_class_id}",
    response_model=NamedMasterResponse,
    operation_id="getMineralClass",
)
def get_mineral_class(mineral_class_id: int, db: DatabaseSession) -> NamedMasterResponse:
    return service.get_item(db, "mineral_class", mineral_class_id)


@router.put(
    "/mineral-classes/{mineral_class_id}",
    response_model=NamedMasterResponse,
    operation_id="updateMineralClass",
)
def update_mineral_class(
    mineral_class_id: int,
    payload: NamedMasterWrite,
    db: DatabaseSession,
) -> NamedMasterResponse:
    return service.update_item(db, "mineral_class", mineral_class_id, payload)


@router.delete(
    "/mineral-classes/{mineral_class_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="deleteMineralClass",
)
def delete_mineral_class(mineral_class_id: int, db: DatabaseSession) -> Response:
    service.delete_item(db, "mineral_class", mineral_class_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/acquisition-methods",
    response_model=list[NamedMasterResponse],
    operation_id="listAcquisitionMethods",
)
def list_acquisition_methods(db: DatabaseSession) -> list[NamedMasterResponse]:
    return service.list_items(db, "acquisition_method")


@router.post(
    "/acquisition-methods",
    response_model=NamedMasterResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="createAcquisitionMethod",
)
def create_acquisition_method(
    payload: NamedMasterWrite, db: DatabaseSession
) -> NamedMasterResponse:
    return service.create_item(db, "acquisition_method", payload)


@router.get(
    "/acquisition-methods/{acquisition_method_id}",
    response_model=NamedMasterResponse,
    operation_id="getAcquisitionMethod",
)
def get_acquisition_method(acquisition_method_id: int, db: DatabaseSession) -> NamedMasterResponse:
    return service.get_item(db, "acquisition_method", acquisition_method_id)


@router.put(
    "/acquisition-methods/{acquisition_method_id}",
    response_model=NamedMasterResponse,
    operation_id="updateAcquisitionMethod",
)
def update_acquisition_method(
    acquisition_method_id: int,
    payload: NamedMasterWrite,
    db: DatabaseSession,
) -> NamedMasterResponse:
    return service.update_item(db, "acquisition_method", acquisition_method_id, payload)


@router.delete(
    "/acquisition-methods/{acquisition_method_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="deleteAcquisitionMethod",
)
def delete_acquisition_method(acquisition_method_id: int, db: DatabaseSession) -> Response:
    service.delete_item(db, "acquisition_method", acquisition_method_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
