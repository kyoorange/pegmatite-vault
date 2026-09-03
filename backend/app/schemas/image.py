import uuid

from pydantic import BaseModel, Field

from app.schemas.specimen import ImageSummary


class ImageUpdate(BaseModel):
    caption: str | None = Field(default=None, max_length=255)


class ImageOrderUpdate(BaseModel):
    image_ids: list[uuid.UUID] = Field(min_length=1)


class ImageRestore(BaseModel):
    specimen_id: uuid.UUID


class ImagePage(BaseModel):
    items: list[ImageSummary]
    page: int
    page_size: int
    total: int


ImageResponse = ImageSummary
