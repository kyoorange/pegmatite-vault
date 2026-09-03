import uuid

from pydantic import BaseModel, Field


class MineralWrite(BaseModel):
    japanese_name: str = Field(min_length=1, max_length=255)
    english_name: str | None = Field(default=None, max_length=255)
    formula: str | None = Field(default=None, max_length=255)
    crystal_system: str | None = Field(default=None, max_length=100)
    mineral_class_id: int | None = Field(default=None, ge=1)
    description: str | None = None


class MineralClassSummary(BaseModel):
    id: int
    name: str
    description: str | None


class MineralResponse(BaseModel):
    id: uuid.UUID
    japanese_name: str
    english_name: str | None
    formula: str | None
    crystal_system: str | None
    mineral_class: MineralClassSummary | None
    description: str | None
    specimen_count: int


class MineralPage(BaseModel):
    items: list[MineralResponse]
    page: int
    page_size: int
    total: int
