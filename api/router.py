from fastapi import APIRouter

from api.routers.health import router as health_router
from api.routers.channels import router as channels_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(channels_router)
