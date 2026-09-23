"""ДАН login flow + OTP (L1) fallback (P0-07).

See app/core/dan_auth.py for the ⛔ external-dependency note: this router works
end-to-end today against the local mock ДАН provider (`dan_use_mock=True`).
Swapping in real ДАН credentials once the agreement lands requires no code
change here — only settings.
"""

import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import dan_auth
from app.core.security import hash_rd, issue_access_token
from app.db.session import get_db
from app.domain.models import User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# In-memory PKCE/state store — swap for Redis before multi-instance deploy.
_pending_flows: dict[str, dan_auth.PkcePair] = {}


class AuthStartResponse(BaseModel):
    authorize_url: str
    state: str


class DanCallbackRequest(BaseModel):
    code: str
    state: str
    redirect_uri: str


class TokenResponse(BaseModel):
    access_token: str
    poe_level: str


class OtpLoginRequest(BaseModel):
    phone: str
    otp_code: str


@router.get("/dan/start", response_model=AuthStartResponse)
async def dan_start(redirect_uri: str):
    pkce = dan_auth.generate_pkce_pair()
    state = secrets.token_urlsafe(16)
    _pending_flows[state] = pkce
    return AuthStartResponse(
        authorize_url=dan_auth.build_authorize_url(redirect_uri=redirect_uri, state=state, pkce=pkce),
        state=state,
    )


@router.post("/dan/callback", response_model=TokenResponse)
async def dan_callback(req: DanCallbackRequest, db: AsyncSession = Depends(get_db)):
    pkce = _pending_flows.pop(req.state, None)
    if pkce is None:
        raise HTTPException(status_code=400, detail="unknown or expired state")

    identity = await dan_auth.exchange_code_for_dan_identity(
        code=req.code, verifier=pkce.verifier, redirect_uri=req.redirect_uri
    )
    raw_rd = identity["rd"]
    rd_hash = hash_rd(raw_rd)
    del raw_rd  # never persisted, never logged past this point

    user = await db.scalar(select(User).where(User.rd_hash == rd_hash))
    if user is None:
        user = User(
            id=uuid.uuid4(), rd_hash=rd_hash, display_name=identity.get("name", "OmniRate user"), poe_level="L2"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    token = issue_access_token(subject_id=str(user.id), rd_hash=rd_hash, poe_level=user.poe_level)
    return TokenResponse(access_token=token, poe_level=user.poe_level)


@router.post("/otp/verify", response_model=TokenResponse)
async def otp_verify(req: OtpLoginRequest, db: AsyncSession = Depends(get_db)):
    """L1 fallback per SOW §7 risk mitigation: if the ДАН agreement slips, the
    pilot can launch on phone+OTP only, with a lower PoE ceiling (L1)."""
    # NOTE: OTP send/verify against an SMS gateway is out of scope for this
    # skeleton — this endpoint assumes an upstream OTP provider already
    # validated req.otp_code and is here to demonstrate the L1 token path.
    pseudo_rd_hash = hash_rd(f"otp:{req.phone}")
    user = await db.scalar(select(User).where(User.rd_hash == pseudo_rd_hash))
    if user is None:
        user = User(id=uuid.uuid4(), rd_hash=pseudo_rd_hash, display_name=req.phone, poe_level="L1")
        db.add(user)
        await db.commit()
        await db.refresh(user)

    token = issue_access_token(subject_id=str(user.id), rd_hash=pseudo_rd_hash, poe_level="L1")
    return TokenResponse(access_token=token, poe_level="L1")
