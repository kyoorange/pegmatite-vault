import uuid

from pydantic import BaseModel, ConfigDict


class MineralOption(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    japanese_name: str
    english_name: str | None = None
    formula: str | None = None


class LocalityOption(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    locality_name: str
    alias_name: str | None = None


class AcquisitionMethodOption(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None


class MineralClassOption(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
