"""ДАН (Mongolia national e-authentication) OAuth2 + PKCE client.

⛔ EXTERNAL DEPENDENCY (see docs/PROGRESS.md): production use requires a signed
agreement with ДАН and real client credentials. Until that lands, `settings.dan_use_mock`
routes the flow at a local mock provider so the rest of the system (JWT issuance,
РД hashing, session handling) can be built and tested end-to-end today.

Risk mitigation per SOW §7: if the ДАН agreement slips, the product falls back to
an OTP-only (L1) verification mode — see `poe_level="L1"` path in the auth router.
"""

import base64
import hashlib
import secrets
from dataclasses import dataclass

import httpx

from app.core.config import get_settings


@dataclass
class PkcePair:
    verifier: str
    challenge: str


def generate_pkce_pair() -> PkcePair:
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(40)).rstrip(b"=").decode()
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    return PkcePair(verifier=verifier, challenge=challenge)


def build_authorize_url(*, redirect_uri: str, state: str, pkce: PkcePair) -> str:
    settings = get_settings()
    return (
        f"{settings.dan_authorize_url}"
        f"?response_type=code&client_id={settings.dan_client_id}"
        f"&redirect_uri={redirect_uri}&state={state}"
        f"&code_challenge={pkce.challenge}&code_challenge_method=S256"
    )


async def exchange_code_for_dan_identity(*, code: str, verifier: str, redirect_uri: str) -> dict:
    """Returns the ДАН identity payload, expected shape: {"rd": "<raw national id>", "name": str}.

    Callers must call `app.core.security.hash_rd` on `rd` immediately and never
    persist or log the raw value.
    """
    settings = get_settings()
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            settings.dan_token_url,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": settings.dan_client_id,
                "code_verifier": verifier,
            },
        )
        resp.raise_for_status()
        return resp.json()
