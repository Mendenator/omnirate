"""PoE evidence attachment (P1-01): verify an e-barimt QR against a review and
bump the review's poe_level accordingly.

Acceptance: TTD must match the entity's registered TTD, receipt age <=90 days,
DDTD globally unique (DB unique constraint -> 409 on replay), every rejection
carries a machine-readable reason code.
"""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import e_barimt
from app.core.config import get_settings
from app.core.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.domain.models import EBarimtReceipt, Entity, PoeEvidence, Review

router = APIRouter(prefix="/api/v1/reviews", tags=["poe-evidence"])


class EBarimtEvidenceRequest(BaseModel):
    qr_payload: str


class EvidenceRejected(Exception):
    def __init__(self, reason_code: str, detail: str):
        self.reason_code = reason_code
        self.detail = detail


@router.post("/{review_id}/evidence/e-barimt", status_code=201)
async def attach_e_barimt_evidence(
    review_id: str,
    req: EBarimtEvidenceRequest,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    review = await db.get(Review, review_id)
    if review is None or review.user_id != user.user_id:
        raise HTTPException(status_code=404, detail="review not found")

    entity = await db.get(Entity, review.entity_id)
    settings = get_settings()

    try:
        receipt = await e_barimt.verify_qr_payload(req.qr_payload)

        if entity.ttd is None or receipt.ttd != entity.ttd:
            raise EvidenceRejected("ttd_mismatch", "receipt merchant does not match this entity")

        age = datetime.now(UTC) - receipt.purchased_at
        if age > timedelta(days=settings.e_barimt_max_receipt_age_days):
            raise EvidenceRejected("receipt_too_old", f"receipt older than {settings.e_barimt_max_receipt_age_days}d")

    except EvidenceRejected as exc:
        raise HTTPException(status_code=422, detail={"reason_code": exc.reason_code, "message": exc.detail}) from exc

    db.add(
        EBarimtReceipt(
            review_id=review.id,
            ddtd=receipt.ddtd,
            ttd=receipt.ttd,
            amount=receipt.amount,
            purchased_at=receipt.purchased_at,
        )
    )
    db.add(PoeEvidence(review_id=review.id, kind="e_barimt", payload={"ddtd": receipt.ddtd, "amount": receipt.amount}))
    review.poe_level = "L4"

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=409, detail={"reason_code": "ddtd_already_used", "message": "this receipt was already used"}
        ) from exc

    return {"poe_level": review.poe_level, "ddtd": receipt.ddtd}
