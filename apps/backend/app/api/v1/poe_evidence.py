"""PoE evidence attachment (P1-01): verify an e-barimt QR against a review and
bump the review's poe_level accordingly.

Acceptance: TTD must match the entity's registered TTD, receipt age <=90 days,
DDTD globally unique (DB unique constraint -> 409 on replay), every rejection
carries a machine-readable reason code.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import e_barimt
from app.core.config import get_settings
from app.core.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.domain.geofence import GpsPing, compute_dwell_seconds, detect_mock_location
from app.domain.models import EBarimtReceipt, Entity, LocationPing, PoeEvidence, Review

MIN_DWELL_SECONDS_FOR_L2 = 5 * 60
GEOFENCE_RADIUS_M = 75

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
) -> dict[str, Any]:
    review = await db.get(Review, review_id)
    if review is None or review.user_id != user.user_id:
        raise HTTPException(status_code=404, detail="review not found")

    entity = await db.get(Entity, review.entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="entity not found")
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


class GpsPingIn(BaseModel):
    lat: float
    lon: float
    accuracy_m: float
    is_mock_provider_flag: bool = False
    recorded_at: datetime


class GpsEvidenceRequest(BaseModel):
    pings: list[GpsPingIn]


@router.post("/{review_id}/evidence/gps", status_code=201)
async def attach_gps_evidence(
    review_id: str,
    req: GpsEvidenceRequest,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    """P2-01/P2-02: dwell-time-based PoE evidence. Rejects outright on any
    mock-location signal (OS flag, impossible speed jump, suspiciously
    uniform accuracy) rather than just discounting it — a spoofed GPS trail
    proves nothing about presence, so partial credit isn't appropriate.
    """
    review = await db.get(Review, review_id)
    if review is None or review.user_id != user.user_id:
        raise HTTPException(status_code=404, detail="review not found")

    entity = await db.get(Entity, review.entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="entity not found")
    if entity.lat is None or entity.lon is None:
        raise HTTPException(
            status_code=422, detail={"reason_code": "no_entity_location", "message": "entity has no geofence center"}
        )

    domain_pings = [
        GpsPing(
            lat=p.lat,
            lon=p.lon,
            accuracy_m=p.accuracy_m,
            is_mock_provider_flag=p.is_mock_provider_flag,
            recorded_at=p.recorded_at,
        )
        for p in req.pings
    ]

    if detect_mock_location(domain_pings):
        raise HTTPException(
            status_code=422,
            detail={"reason_code": "mock_location_detected", "message": "GPS trail failed spoofing checks"},
        )

    dwell_seconds = compute_dwell_seconds(
        domain_pings, center_lat=float(entity.lat), center_lon=float(entity.lon), radius_m=GEOFENCE_RADIUS_M
    )

    for p in req.pings:
        db.add(
            LocationPing(
                review_id=review.id,
                lat=p.lat,
                lon=p.lon,
                accuracy_m=p.accuracy_m,
                is_mock_provider_flag=p.is_mock_provider_flag,
                recorded_at=p.recorded_at,
            )
        )

    if dwell_seconds < MIN_DWELL_SECONDS_FOR_L2:
        await db.commit()
        raise HTTPException(
            status_code=422,
            detail={
                "reason_code": "insufficient_dwell_time",
                "message": f"only {dwell_seconds:.0f}s in geofence, need {MIN_DWELL_SECONDS_FOR_L2}s",
            },
        )

    db.add(PoeEvidence(review_id=review.id, kind="gps", payload={"dwell_seconds": dwell_seconds}))
    if review.poe_level in ("L0", "L1"):
        review.poe_level = "L2"
    await db.commit()

    return {"poe_level": review.poe_level, "dwell_seconds": dwell_seconds}
