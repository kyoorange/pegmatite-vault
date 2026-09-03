from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.acquisition_method import AcquisitionMethod
from app.models.locality import Locality
from app.models.mineral import Mineral
from app.models.mineral_class import MineralClass
from app.schemas.master import (
    AcquisitionMethodOption,
    LocalityOption,
    MineralClassOption,
    MineralOption,
)

router = APIRouter(prefix="/options", tags=["Masters"])
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get("/minerals", response_model=list[MineralOption], operation_id="listMineralOptions")
def list_minerals(db: DatabaseSession) -> list[Mineral]:
    return list(db.scalars(select(Mineral).order_by(Mineral.japanese_name)))


@router.get(
    "/mineral-classes",
    response_model=list[MineralClassOption],
    operation_id="listMineralClassOptions",
)
def list_mineral_classes(db: DatabaseSession) -> list[MineralClass]:
    return list(db.scalars(select(MineralClass).order_by(MineralClass.id)))


@router.get("/localities", response_model=list[LocalityOption], operation_id="listLocalityOptions")
def list_localities(db: DatabaseSession) -> list[Locality]:
    return list(db.scalars(select(Locality).order_by(Locality.locality_name)))


@router.get(
    "/acquisition-methods",
    response_model=list[AcquisitionMethodOption],
    operation_id="listAcquisitionMethodOptions",
)
def list_acquisition_methods(db: DatabaseSession) -> list[AcquisitionMethod]:
    return list(db.scalars(select(AcquisitionMethod).order_by(AcquisitionMethod.id)))
