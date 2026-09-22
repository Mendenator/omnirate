"""Moderator queue API (P2-12). Note: moderator authorization (only staff
accounts may call these) is not yet wired — CurrentUser has no role field
yet (see docs/PROGRESS.md); adding one is a P3 admin-hardening task, not
blocked on anything external.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.domain.models import ModerationCase, ModerationDecision
from app.domain.moderation_queue import CaseState, Decision, Verdict, resolve_case

router = APIRouter(prefix="/api/v1/moderation", tags=["moderation-queue"])


class CaseResponse(BaseModel):
    id: str
    review_id: str
    state: str

    model_config = {"from_attributes": True}


@router.get("/queue", response_model=list[CaseResponse])
async def list_queue(db: AsyncSession = Depends(get_db)):
    cases = (
        await db.execute(
            select(ModerationCase)
            .where(ModerationCase.state.in_(["awaiting_first_decision", "awaiting_second_decision"]))
            .order_by(ModerationCase.created_at)
            .limit(50)
        )
    ).scalars().all()
    return cases


class DecideRequest(BaseModel):
    verdict: str


@router.post("/cases/{case_id}/decide", response_model=CaseResponse)
async def decide_case(
    case_id: str, req: DecideRequest, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)
):
    case = await db.get(ModerationCase, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="case not found")
    if case.state in ("resolved", "escalated"):
        raise HTTPException(status_code=409, detail=f"case already {case.state}")

    decision = ModerationDecision(case_id=case.id, moderator_id=user.user_id, verdict=req.verdict)
    db.add(decision)
    try:
        await db.flush()
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="this moderator already decided this case") from exc

    existing = (
        await db.execute(select(ModerationDecision).where(ModerationDecision.case_id == case.id).order_by(ModerationDecision.decided_at))
    ).scalars().all()
    domain_decisions = [Decision(moderator_id=str(d.moderator_id), verdict=Verdict(d.verdict)) for d in existing]

    outcome = resolve_case(domain_decisions)
    case.state = outcome.state.value
    case.final_verdict = outcome.final_verdict.value if outcome.final_verdict else None
    if outcome.state in (CaseState.RESOLVED, CaseState.ESCALATED):
        case.resolved_at = datetime.now(UTC)

    await db.commit()
    return case
