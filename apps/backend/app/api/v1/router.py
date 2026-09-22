from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.complaints import router as complaints_router
from app.api.v1.entities import router as entities_router
from app.api.v1.hospital_qr import router as hospital_qr_router
from app.api.v1.moderation_queue import router as moderation_queue_router
from app.api.v1.ownership import router as ownership_router
from app.api.v1.poe_evidence import router as poe_evidence_router
from app.api.v1.reviews import router as reviews_router
from app.api.v1.search import router as search_router
from app.api.v1.uploads import router as uploads_router
from app.schema_registry.router import router as schema_registry_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(entities_router)
api_router.include_router(reviews_router)
api_router.include_router(poe_evidence_router)
api_router.include_router(ownership_router)
api_router.include_router(complaints_router)
api_router.include_router(uploads_router)
api_router.include_router(search_router)
api_router.include_router(hospital_qr_router)
api_router.include_router(moderation_queue_router)
api_router.include_router(schema_registry_router)
