from typing import Literal

from pydantic import BaseModel, Field


class StorageStatus(BaseModel):
    path: str
    writable: bool
    used_bytes: int
    free_bytes: int
    active_image_count: int
    archived_image_count: int


class SystemStatus(BaseModel):
    version: str
    database: Literal["ok"]
    image_storage: StorageStatus


class StorageTargetRequest(BaseModel):
    path: str = Field(min_length=1, max_length=1000)


class StorageMigrationPreview(BaseModel):
    source_path: str
    target_path: str
    file_count: int
    total_bytes: int
    free_bytes: int
    same_path: bool
    ready: bool
    issues: list[str]
