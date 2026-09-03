import shutil
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.storage import (
    image_storage_is_writable,
    migrate_storage,
    validate_storage_target,
)
from app.db.session import get_db
from app.models.image import Image
from app.schemas.settings import (
    StorageMigrationPreview,
    StorageStatus,
    StorageTargetRequest,
    SystemStatus,
)

router = APIRouter(prefix="/settings", tags=["System"])
DatabaseSession = Annotated[Session, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]


def _directory_size(path: Path) -> int:
    total = 0
    if not path.exists():
        return total
    for item in path.rglob("*"):
        try:
            if item.is_file():
                total += item.stat().st_size
        except OSError:
            continue
    return total


@router.get("/status", response_model=SystemStatus, operation_id="getSystemStatus")
def get_system_status(db: DatabaseSession, settings: AppSettings) -> SystemStatus:
    db.execute(text("SELECT 1"))
    images_directory = settings.images_directory
    storage_root = images_directory.parent
    disk_usage = shutil.disk_usage(storage_root)
    counts = dict(db.execute(select(Image.status, func.count()).group_by(Image.status)).all())
    return SystemStatus(
        version="0.1.0",
        database="ok",
        image_storage=StorageStatus(
            path=str(storage_root),
            writable=image_storage_is_writable(settings),
            used_bytes=_directory_size(images_directory),
            free_bytes=disk_usage.free,
            active_image_count=counts.get("active", 0),
            archived_image_count=counts.get("archived", 0),
        ),
    )


@router.post(
    "/storage/validate",
    response_model=StorageMigrationPreview,
    operation_id="validateImageStorageTarget",
)
def validate_image_storage_target(
    payload: StorageTargetRequest, settings: AppSettings
) -> StorageMigrationPreview:
    return StorageMigrationPreview(**validate_storage_target(settings, payload.path))


@router.post(
    "/storage/migrate",
    response_model=StorageMigrationPreview,
    operation_id="migrateImageStorage",
)
def migrate_image_storage(
    payload: StorageTargetRequest, settings: AppSettings
) -> StorageMigrationPreview:
    return StorageMigrationPreview(**migrate_storage(settings, payload.path))
