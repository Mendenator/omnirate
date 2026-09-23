"""РД (national ID) hashing and JWT issuance.

SOW acceptance (P0-07): "DB бүрэн scan-д түүхий РД 0 мөр" — raw РД must never be
persisted. `hash_rd` is the only place the raw value is allowed to be seen; the
caller must discard the plaintext immediately after calling this.
"""

import hashlib
import hmac
import time
import uuid

import jwt

from app.core.config import get_settings


def hash_rd(raw_rd: str) -> str:
    settings = get_settings()
    digest = hmac.new(settings.rd_hmac_secret.encode(), raw_rd.strip().encode(), hashlib.sha256)
    return digest.hexdigest()


def issue_access_token(*, subject_id: str, rd_hash: str, poe_level: str) -> str:
    settings = get_settings()
    now = int(time.time())
    claims = {
        "sub": subject_id,
        "rd_hash": rd_hash,
        "poe_level": poe_level,
        "iat": now,
        "exp": now + settings.jwt_access_ttl_seconds,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
