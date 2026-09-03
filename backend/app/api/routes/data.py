from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.schemas.data_import import ImportCommit, ImportResult, ImportValidation
from app.services.data_export import build_export
from app.services.data_import import commit_import, validate_import

router = APIRouter(prefix="/data", tags=["Data management"])
DatabaseSession = Annotated[Session, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]


@router.post("/export", operation_id="exportData")
def export_data(db: DatabaseSession) -> Response:
    content, filename = build_export(db)
    return Response(
        content=content,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post(
    "/import/validate",
    response_model=ImportValidation,
    operation_id="validateImport",
)
def validate_data_import(
    db: DatabaseSession,
    settings: AppSettings,
    file: Annotated[UploadFile, File()],
) -> ImportValidation:
    return validate_import(db, settings, file)


@router.post(
    "/import/commit",
    response_model=ImportResult,
    operation_id="commitImport",
)
def commit_data_import(
    payload: ImportCommit, db: DatabaseSession, settings: AppSettings
) -> ImportResult:
    return commit_import(db, settings, payload.commit_token)
