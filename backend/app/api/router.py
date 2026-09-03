from fastapi import APIRouter

from app.api.routes.data import router as data_router
from app.api.routes.health import router as health_router
from app.api.routes.images import router as images_router
from app.api.routes.localities import router as localities_router
from app.api.routes.masters import router as masters_router
from app.api.routes.minerals import router as minerals_router
from app.api.routes.named_masters import router as named_masters_router
from app.api.routes.settings import router as settings_router
from app.api.routes.specimens import router as specimens_router

api_router = APIRouter()
api_router.include_router(data_router)
api_router.include_router(health_router)
api_router.include_router(specimens_router)
api_router.include_router(masters_router)
api_router.include_router(images_router)
api_router.include_router(minerals_router)
api_router.include_router(localities_router)
api_router.include_router(named_masters_router)
api_router.include_router(settings_router)
