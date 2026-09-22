"""Hospital-visit QR issue + verify (P2-03)."""

import base64
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_current_user
from app.core.hospital_qr import QrVerificationError, generate_hospital_qr, verify_hospital_qr
from app.core.hospital_qr_pdf import render_qr_pdf
from app.db.session import get_db
from app.domain.models import Entity, EntityOwner, HospitalQrToken

router = APIRouter(prefix="/api/v1", tags=["hospital-qr"])


class IssueQrResponse(BaseModel):
    token: str
    expires_at: str
    pdf_base64: str


@router.post("/entities/{entity_id}/hospital-qr", response_model=IssueQrResponse, status_code=201)
async def issue_hospital_qr(
    entity_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)
):
    entity = await db.get(Entity, entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="entity not found")

    owner = await db.scalar(
        select(EntityOwner).where(EntityOwner.entity_id == entity_id, EntityOwner.user_id == user.user_id)
    )
    if owner is None:
        raise HTTPException(status_code=403, detail="only the verified owner can issue a visit QR")

    token = generate_hospital_qr(entity_id)
    # Immediately self-verify to recover the parsed claims rather than
    # re-implementing the base64/JSON decode here — one code path for
    # "what does this token contain," used by both issuer and verifier.
    payload = verify_hospital_qr(token)

    db.add(
        HospitalQrToken(
            jti=payload.jti,
            entity_id=entity_id,
            issued_at=datetime.fromtimestamp(payload.issued_at, tz=UTC),
            expires_at=datetime.fromtimestamp(payload.expires_at, tz=UTC),
        )
    )
    await db.commit()

    expires_label = datetime.fromtimestamp(payload.expires_at, tz=UTC).isoformat()
    pdf_bytes = render_qr_pdf(token, entity_name=entity.name, expires_at_label=expires_label)

    return IssueQrResponse(token=token, expires_at=expires_label, pdf_base64=base64.b64encode(pdf_bytes).decode())


class VerifyQrRequest(BaseModel):
    token: str


@router.post("/hospital-qr/verify")
async def verify_qr(req: VerifyQrRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = verify_hospital_qr(req.token)
    except QrVerificationError as exc:
        raise HTTPException(status_code=422, detail={"reason_code": exc.reason_code}) from exc

    # Atomic claim: only succeeds if this jti exists and hasn't been used yet.
    # A second concurrent verify of the same token affects 0 rows here, so
    # replay is rejected even under a race, not just on the happy path.
    result = await db.execute(
        update(HospitalQrToken)
        .where(HospitalQrToken.jti == payload.jti, HospitalQrToken.used_at.is_(None))
        .values(used_at=datetime.now(UTC))
    )
    await db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=422, detail={"reason_code": "jti_replayed_or_unknown"})

    return {"entity_id": payload.entity_id, "status": "verified"}
