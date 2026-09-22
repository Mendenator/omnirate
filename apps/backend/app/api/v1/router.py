from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.entities import router as entities_router
from app.api.v1.reviews import router as reviews_router
from app.schema_registry.router import router as schema_registry_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(entities_router)
api_router.include_router(reviews_router)
api_router.include_router(schema_registry_router)
