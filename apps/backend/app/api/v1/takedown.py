"""Takedown + law-enforcement portal endpoints (P3-05/P3-06)."""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.domain.audit import append_audit_log
from app.domain.models import TakedownRequest
from app.domain.takedown import RequesterType, TakedownStatus, compute_sla_deadline

router = APIRouter(prefix="/api/v1", tags=["takedown"])


class TakedownCreateRequest(BaseModel):
    target_type: str
    target_id: str
    reason: str


class LawEnforcementRequestCreate(BaseModel):
    target_type: str
    target_id: str
    reason: str
    case_reference: str  # required — distinguishes this portal from the public takedown form


class TakedownResponse(BaseModel):
    # Both endpoints below return the raw ORM row — id is uuid.UUID and
    # sla_deadline is datetime, not str. See ComplaintResponse in
    # app/api/v1/complaints.py for why a plain `str` field rejects them.
    id: uuid.UUID
    status: str
    sla_deadline: datetime

    model_config = {"from_attributes": True}


@router.post("/takedowns", response_model=TakedownResponse, status_code=201)
async def create_takedown(
    req: TakedownCreateRequest, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)
) -> TakedownRequest:
    now = datetime.now(UTC)
    takedown = TakedownRequest(
        requester_id=user.user_id,
        requester_type=RequesterType.USER.value,
        target_type=req.target_type,
        target_id=req.target_id,
        reason=req.reason,
        sla_deadline=compute_sla_deadline(requester_type=RequesterType.USER, created_at=now),
    )
    db.add(takedown)
    await db.flush()
    await append_audit_log(
        db,
        actor_id=user.user_id,
        action="takedown.create",
        target_type=req.target_type,
        target_id=req.target_id,
        payload={"takedown_id": str(takedown.id), "requester_type": "user"},
    )
    await db.commit()
    return takedown


@router.post("/law-enforcement-requests", response_model=TakedownResponse, status_code=201)
async def create_law_enforcement_request(
    req: LawEnforcementRequestCreate, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)
) -> TakedownRequest:
    """No separate law-enforcement auth mechanism exists yet (see
    docs/PROGRESS.md — role-based access is a P3 admin-hardening gap this
    inherits from P2-12's moderator queue). `case_reference` being required
    is a paper trail, not itself an authorization check."""
    now = datetime.now(UTC)
    takedown = TakedownRequest(
        requester_id=user.user_id,
        requester_type=RequesterType.LAW_ENFORCEMENT.value,
        target_type=req.target_type,
        target_id=req.target_id,
        reason=req.reason,
        case_reference=req.case_reference,
        sla_deadline=compute_sla_deadline(requester_type=RequesterType.LAW_ENFORCEMENT, created_at=now),
    )
    db.add(takedown)
    await db.flush()
    await append_audit_log(
        db,
        actor_id=user.user_id,
        action="takedown.create",
        target_type=req.target_type,
        target_id=req.target_id,
        payload={
            "takedown_id": str(takedown.id),
            "requester_type": "law_enforcement",
            "case_reference": req.case_reference,
        },
    )
    await db.commit()
    return takedown


class ResolveTakedownRequest(BaseModel):
    status: str  # "resolved" | "rejected"


@router.post("/takedowns/{takedown_id}/resolve", response_model=TakedownResponse)
async def resolve_takedown(
    takedown_id: str,
    req: ResolveTakedownRequest,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> TakedownRequest:
    takedown = await db.get(TakedownRequest, takedown_id)
    if takedown is None:
        raise HTTPException(status_code=404, detail="takedown request not found")
    if takedown.status in (TakedownStatus.RESOLVED.value, TakedownStatus.REJECTED.value):
        raise HTTPException(status_code=409, detail=f"already {takedown.status}")

    takedown.status = req.status
    takedown.resolved_at = datetime.now(UTC)
    await append_audit_log(
        db,
        actor_id=user.user_id,
        action="takedown.resolve",
        target_type=takedown.target_type,
        target_id=str(takedown.target_id),
        payload={"takedown_id": takedown_id, "status": req.status},
    )
    await db.commit()
    return takedown
