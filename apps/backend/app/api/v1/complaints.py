"""Complaint endpoint, base version (P1-14). Rate-limited by the same gateway
middleware as every other route (app/core/rate_limit.py); full triage queue
UX lands with P2-12.
"""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.domain.models import Complaint

router = APIRouter(prefix="/api/v1/complaints", tags=["complaints"])


class ComplaintCreateRequest(BaseModel):
    target_type: str = Field(pattern="^(review|entity)$")
    target_id: str
    reason: str
    details: str | None = None


class ComplaintResponse(BaseModel):
    # Complaint.id is a uuid.UUID column — a plain `str` field rejects it
    # outright under Pydantic v2 (no UUID->str coercion), which only ever
    # surfaced once this endpoint ran against a real Postgres row instead of
    # a ConnectionRefusedError before reaching response serialization.
    id: uuid.UUID
    status: str

    model_config = {"from_attributes": True}


@router.post("", response_model=ComplaintResponse, status_code=201)
async def create_complaint(
    req: ComplaintCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Complaint:
    complaint = Complaint(
        reporter_id=user.user_id,
        target_type=req.target_type,
        target_id=req.target_id,
        reason=req.reason,
        details=req.details,
    )
    db.add(complaint)
    await db.commit()
    await db.refresh(complaint)
    return complaint
