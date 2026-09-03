import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.schemas.image import (
    ImageOrderUpdate,
    ImagePage,
    ImageResponse,
    ImageRestore,
    ImageUpdate,
)
from app.services import images as service

router = APIRouter(tags=["Images"])
DatabaseSession = Annotated[Session, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]


@router.post(
    "/specimens/{specimen_id}/images",
    response_model=ImageResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="uploadSpecimenImage",
)
def upload_specimen_image(
    specimen_id: uuid.UUID,
    db: DatabaseSession,
    settings: AppSettings,
    file: Annotated[UploadFile, File()],
    caption: Annotated[str | None, Form()] = None,
) -> ImageResponse:
    return service.upload_image(db, settings, specimen_id, file, caption)


@router.patch(
    "/specimens/{specimen_id}/images/order",
    response_model=list[ImageResponse],
    operation_id="reorderSpecimenImages",
)
def reorder_specimen_images(
    specimen_id: uuid.UUID,
    payload: ImageOrderUpdate,
    db: DatabaseSession,
) -> list[ImageResponse]:
    return service.reorder_images(db, specimen_id, payload.image_ids)


@router.patch("/images/{image_id}", response_model=ImageResponse, operation_id="updateImage")
def update_image(image_id: uuid.UUID, payload: ImageUpdate, db: DatabaseSession) -> ImageResponse:
    return service.update_caption(db, image_id, payload.caption)


@router.delete(
    "/images/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="archiveImage",
)
def archive_image(image_id: uuid.UUID, db: DatabaseSession) -> Response:
    service.archive_image(db, image_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/images/{image_id}/content", operation_id="getImageContent")
def get_image_content(
    image_id: uuid.UUID,
    variant: Literal["original", "display", "thumbnail"],
    db: DatabaseSession,
    settings: AppSettings,
) -> FileResponse:
    path, media_type = service.get_content_path(db, settings, image_id, variant)
    return FileResponse(path, media_type=media_type)


@router.get(
    "/archived-images",
    response_model=ImagePage,
    operation_id="listArchivedImages",
)
def list_archived_images(
    db: DatabaseSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 24,
) -> ImagePage:
    return service.list_archived_images(db, page=page, page_size=page_size)


@router.get("/archived-images/{image_id}/content", operation_id="getArchivedImageContent")
def get_archived_image_content(
    image_id: uuid.UUID,
    variant: Literal["original", "display", "thumbnail"],
    db: DatabaseSession,
    settings: AppSettings,
) -> FileResponse:
    path, media_type = service.get_archived_content_path(db, settings, image_id, variant)
    return FileResponse(path, media_type=media_type)


@router.post(
    "/images/{image_id}/restore",
    response_model=ImageResponse,
    operation_id="restoreImage",
)
def restore_image(image_id: uuid.UUID, payload: ImageRestore, db: DatabaseSession) -> ImageResponse:
    return service.restore_image(db, image_id, payload.specimen_id)


@router.delete(
    "/images/{image_id}/permanent",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="permanentlyDeleteImage",
)
def permanently_delete_image(
    image_id: uuid.UUID, db: DatabaseSession, settings: AppSettings
) -> Response:
    service.permanently_delete_image(db, settings, image_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
