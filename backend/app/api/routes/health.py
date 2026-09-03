from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.storage import image_storage_is_writable
from app.db.session import get_db
from app.schemas.health import HealthResponse

router = APIRouter(tags=["System"])


@router.get("/health", response_model=HealthResponse, operation_id="getHealth")
def get_health(
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> HealthResponse:
    db.execute(text("SELECT 1"))
    storage_status = "ok" if image_storage_is_writable(settings) else "unavailable"
    return HealthResponse(
        status="ok" if storage_status == "ok" else "degraded",
        database="ok",
        image_storage=storage_status,
    )
