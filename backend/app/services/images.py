import io
import logging
import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import UploadFile
from PIL import Image as PillowImage
from PIL import UnidentifiedImageError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import (
    ImageTooLargeError,
    InvalidImageError,
    InvalidReferenceError,
    ResourceNotFoundError,
)
from app.core.storage import synchronized_storage
from app.models.image import Image
from app.models.specimen import Specimen
from app.schemas.image import ImagePage
from app.schemas.specimen import ImageSummary

logger = logging.getLogger(__name__)

FORMAT_CONFIG = {
    "JPEG": ("jpg", "image/jpeg"),
    "PNG": ("png", "image/png"),
    "WEBP": ("webp", "image/webp"),
}


def _response(image: Image) -> ImageSummary:
    return ImageSummary(
        id=image.id,
        specimen_id=image.specimen_id,
        archived_from_specimen_id=image.archived_from_specimen_id,
        original_filename=image.original_filename,
        media_type=image.media_type,
        file_size=image.file_size,
        caption=image.caption,
        sort_order=image.sort_order,
        status=image.status,
        archived_at=image.archived_at,
        created_at=image.created_at,
    )


def _directory(settings: Settings, image_id: uuid.UUID) -> Path:
    return settings.images_directory / str(image_id)


def _variant_path(settings: Settings, image: Image, variant: str) -> Path:
    directory = _directory(settings, image.id)
    if variant == "original":
        return directory / f"original.{image.original_extension}"
    if variant in {"display", "thumbnail"}:
        return directory / f"{variant}.webp"
    raise InvalidImageError("Unknown image variant.")


def _read_upload(file: UploadFile, max_bytes: int) -> bytes:
    data = file.file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ImageTooLargeError
    if not data:
        raise InvalidImageError("Empty image.")
    return data


def _inspect(data: bytes) -> tuple[PillowImage.Image, str, str]:
    try:
        image = PillowImage.open(io.BytesIO(data))
        image.verify()
        image = PillowImage.open(io.BytesIO(data))
        image.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise InvalidImageError("Unsupported or invalid image.") from exc
    if image.format not in FORMAT_CONFIG:
        raise InvalidImageError("Unsupported image format.")
    extension, media_type = FORMAT_CONFIG[image.format]
    return image, extension, media_type


def _save_variant(image: PillowImage.Image, path: Path, max_px: int) -> None:
    converted = image.copy()
    converted.thumbnail((max_px, max_px), PillowImage.Resampling.LANCZOS)
    if converted.mode not in {"RGB", "RGBA"}:
        converted = converted.convert("RGB")
    converted.save(path, format="WEBP", quality=85, method=6)


@synchronized_storage
def upload_image(
    db: Session,
    settings: Settings,
    specimen_id: uuid.UUID,
    file: UploadFile,
    caption: str | None,
) -> ImageSummary:
    if db.get(Specimen, specimen_id) is None:
        raise ResourceNotFoundError("specimen", specimen_id)
    data = _read_upload(file, settings.image_max_upload_bytes)
    pillow_image, extension, media_type = _inspect(data)
    image_id = uuid.uuid4()
    directory = _directory(settings, image_id)
    directory.mkdir(parents=True, exist_ok=False)
    try:
        (directory / f"original.{extension}").write_bytes(data)
        _save_variant(pillow_image, directory / "display.webp", settings.image_display_max_px)
        _save_variant(
            pillow_image,
            directory / "thumbnail.webp",
            settings.image_thumbnail_max_px,
        )
        current_max = db.scalar(
            select(func.max(Image.sort_order)).where(
                Image.specimen_id == specimen_id, Image.status == "active"
            )
        )
        sort_order = (current_max if current_max is not None else -1) + 1
        image = Image(
            id=image_id,
            specimen_id=specimen_id,
            original_filename=Path(file.filename or f"image.{extension}").name,
            original_extension=extension,
            media_type=media_type,
            file_size=len(data),
            caption=caption,
            sort_order=sort_order,
            status="active",
        )
        db.add(image)
        db.commit()
        db.refresh(image)
    except Exception:
        db.rollback()
        shutil.rmtree(directory, ignore_errors=True)
        raise
    return _response(image)


def get_active_image(db: Session, image_id: uuid.UUID) -> Image:
    image = db.get(Image, image_id)
    if image is None or image.status != "active":
        raise ResourceNotFoundError("image", image_id)
    return image


def get_archived_image(db: Session, image_id: uuid.UUID) -> Image:
    image = db.get(Image, image_id)
    if image is None or image.status != "archived":
        raise ResourceNotFoundError("archived_image", image_id)
    return image


def get_content_path(
    db: Session, settings: Settings, image_id: uuid.UUID, variant: str
) -> tuple[Path, str]:
    image = get_active_image(db, image_id)
    path = _variant_path(settings, image, variant)
    if not path.exists() and variant != "original":
        original = _variant_path(settings, image, "original")
        if not original.exists():
            raise ResourceNotFoundError("image_file", image_id)
        pillow_image = PillowImage.open(original)
        max_px = (
            settings.image_display_max_px
            if variant == "display"
            else settings.image_thumbnail_max_px
        )
        _save_variant(pillow_image, path, max_px)
    if not path.exists():
        raise ResourceNotFoundError("image_file", image_id)
    media_type = image.media_type if variant == "original" else "image/webp"
    return path, media_type


def get_archived_content_path(
    db: Session, settings: Settings, image_id: uuid.UUID, variant: str
) -> tuple[Path, str]:
    image = get_archived_image(db, image_id)
    path = _variant_path(settings, image, variant)
    if not path.exists() and variant != "original":
        original = _variant_path(settings, image, "original")
        if not original.exists():
            raise ResourceNotFoundError("image_file", image_id)
        pillow_image = PillowImage.open(original)
        max_px = (
            settings.image_display_max_px
            if variant == "display"
            else settings.image_thumbnail_max_px
        )
        _save_variant(pillow_image, path, max_px)
    if not path.exists():
        raise ResourceNotFoundError("image_file", image_id)
    return path, image.media_type if variant == "original" else "image/webp"


def update_caption(db: Session, image_id: uuid.UUID, caption: str | None) -> ImageSummary:
    image = get_active_image(db, image_id)
    image.caption = caption
    db.commit()
    db.refresh(image)
    return _response(image)


def archive_image(db: Session, image_id: uuid.UUID) -> None:
    image = get_active_image(db, image_id)
    image.archived_from_specimen_id = image.specimen_id
    image.specimen_id = None
    image.status = "archived"
    image.archived_at = datetime.now(UTC)
    db.commit()


def reorder_images(
    db: Session, specimen_id: uuid.UUID, image_ids: list[uuid.UUID]
) -> list[ImageSummary]:
    images = list(
        db.scalars(
            select(Image).where(
                Image.specimen_id == specimen_id,
                Image.status == "active",
            )
        )
    )
    existing_ids = {image.id for image in images}
    if len(image_ids) != len(set(image_ids)) or set(image_ids) != existing_ids:
        raise InvalidReferenceError("image_order", list(image_ids))
    by_id = {image.id: image for image in images}
    for position, image_id in enumerate(image_ids):
        by_id[image_id].sort_order = position
    db.commit()
    return [_response(by_id[image_id]) for image_id in image_ids]


def list_archived_images(db: Session, *, page: int, page_size: int) -> ImagePage:
    condition = Image.status == "archived"
    total = db.scalar(select(func.count()).select_from(Image).where(condition)) or 0
    statement = (
        select(Image)
        .where(condition)
        .order_by(Image.archived_at.desc(), Image.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return ImagePage(
        items=[_response(image) for image in db.scalars(statement)],
        page=page,
        page_size=page_size,
        total=total,
    )


def restore_image(db: Session, image_id: uuid.UUID, specimen_id: uuid.UUID) -> ImageSummary:
    image = get_archived_image(db, image_id)
    if db.get(Specimen, specimen_id) is None:
        raise ResourceNotFoundError("specimen", specimen_id)
    current_max = db.scalar(
        select(func.max(Image.sort_order)).where(
            Image.specimen_id == specimen_id,
            Image.status == "active",
        )
    )
    image.specimen_id = specimen_id
    image.archived_from_specimen_id = None
    image.status = "active"
    image.archived_at = None
    image.sort_order = (current_max if current_max is not None else -1) + 1
    db.commit()
    db.refresh(image)
    return _response(image)


@synchronized_storage
def permanently_delete_image(db: Session, settings: Settings, image_id: uuid.UUID) -> None:
    image = get_archived_image(db, image_id)
    source = _directory(settings, image.id)
    trash_root = settings.images_directory / ".trash"
    staged = trash_root / f"{image.id}-{uuid.uuid4()}"
    moved = False
    try:
        if source.exists():
            trash_root.mkdir(parents=True, exist_ok=True)
            source.rename(staged)
            moved = True
        db.delete(image)
        db.commit()
    except Exception:
        db.rollback()
        if moved and staged.exists():
            staged.rename(source)
        raise
    if moved:
        try:
            shutil.rmtree(staged)
        except OSError:
            logger.warning("Failed to remove staged image directory: %s", staged)
