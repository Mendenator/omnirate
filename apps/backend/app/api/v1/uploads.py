from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.uploads import finalize_upload, presign_upload

router = APIRouter(prefix="/api/v1/uploads", tags=["uploads"])

_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


class PresignRequest(BaseModel):
    content_type: str


class PresignResponse(BaseModel):
    upload_id: str
    upload_url: str


class FinalizeResponse(BaseModel):
    object_key: str


@router.post("/presign", response_model=PresignResponse)
async def presign(req: PresignRequest) -> PresignResponse:
    if req.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=422, detail=f"content_type must be one of {sorted(_ALLOWED_CONTENT_TYPES)}")
    upload_id, url = presign_upload(content_type=req.content_type)
    return PresignResponse(upload_id=upload_id, upload_url=url)


@router.post("/{upload_id}/finalize", response_model=FinalizeResponse)
async def finalize(upload_id: str) -> FinalizeResponse:
    try:
        key = finalize_upload(upload_id=upload_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return FinalizeResponse(object_key=key)
