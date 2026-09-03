import uuid
from decimal import Decimal

from pydantic import BaseModel, Field


class LocalityWrite(BaseModel):
    locality_name: str = Field(min_length=1, max_length=255)
    alias_name: str | None = Field(default=None, max_length=255)
    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)
    note: str | None = None


class LocalityResponse(BaseModel):
    id: uuid.UUID
    locality_name: str
    alias_name: str | None
    latitude: Decimal | None
    longitude: Decimal | None
    note: str | None
    specimen_count: int


class LocalityPage(BaseModel):
    items: list[LocalityResponse]
    page: int
    page_size: int
    total: int
