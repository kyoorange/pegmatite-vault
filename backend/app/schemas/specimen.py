import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class LocalitySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    locality_name: str
    alias_name: str | None = None


class AcquisitionMethodSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None


class MineralSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    japanese_name: str
    english_name: str | None = None
    formula: str | None = None


class ImageSummary(BaseModel):
    id: uuid.UUID
    specimen_id: uuid.UUID | None
    archived_from_specimen_id: uuid.UUID | None = None
    original_filename: str
    media_type: str
    file_size: int
    caption: str | None
    sort_order: int
    status: str
    archived_at: datetime | None
    created_at: datetime


class SpecimenWrite(BaseModel):
    specimen_no: int | None = Field(default=None, ge=1)
    specimen_name: str = Field(min_length=1, max_length=255)
    locality_id: uuid.UUID | None = None
    acquisition_method_id: int | None = Field(default=None, ge=1)
    collection_date: date | None = None
    features: str | None = None
    note: str | None = None
    favorite: bool = False
    mineral_ids: list[uuid.UUID] = Field(default_factory=list)


class SpecimenCreate(SpecimenWrite):
    pass


class SpecimenUpdate(BaseModel):
    specimen_no: int | None = Field(default=None, ge=1)
    specimen_name: str | None = Field(default=None, min_length=1, max_length=255)
    locality_id: uuid.UUID | None = None
    acquisition_method_id: int | None = Field(default=None, ge=1)
    collection_date: date | None = None
    features: str | None = None
    note: str | None = None
    favorite: bool | None = None
    mineral_ids: list[uuid.UUID] | None = None


class SpecimenSummary(BaseModel):
    id: uuid.UUID
    specimen_no: int
    specimen_name: str
    locality: LocalitySummary | None
    favorite: bool
    mineral_names: list[str]
    thumbnail_image_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class SpecimenDetail(SpecimenSummary):
    acquisition_method: AcquisitionMethodSummary | None
    collection_date: date | None
    features: str | None
    note: str | None
    minerals: list[MineralSummary]
    images: list[ImageSummary]


class SpecimenPage(BaseModel):
    items: list[SpecimenSummary]
    page: int
    page_size: int
    total: int
