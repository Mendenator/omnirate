"""Hospital-visit QR: Ed25519-signed, 72h-expiring, single-use (P2-03).

A JWT library was deliberately not reused here — Ed25519 ("EdDSA") support
across JWT libraries is inconsistent, and the token only needs three claims,
so a minimal base64(payload).base64(signature) format keeps the crypto
auditable in ~20 lines rather than trusting a library's algorithm-negotiation
path. Replay protection is a DB unique constraint on `jti` (app/api/v1/hospital_qr.py),
not just an expiry check — acceptance requires expired *and* replayed jti both
rejected 100%.
"""

import base64
import json
import time
import uuid
from dataclasses import dataclass

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.core.config import get_settings


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _get_private_key() -> Ed25519PrivateKey:
    seed = _b64decode(get_settings().hospital_qr_ed25519_seed_b64)
    return Ed25519PrivateKey.from_private_bytes(seed)


@dataclass(frozen=True)
class HospitalQrPayload:
    entity_id: str
    jti: str
    issued_at: int
    expires_at: int


class QrVerificationError(Exception):
    def __init__(self, reason_code: str):
        self.reason_code = reason_code


def generate_hospital_qr(entity_id: str) -> str:
    settings = get_settings()
    now = int(time.time())
    payload = HospitalQrPayload(
        entity_id=entity_id,
        jti=str(uuid.uuid4()),
        issued_at=now,
        expires_at=now + settings.hospital_qr_ttl_hours * 3600,
    )
    payload_bytes = json.dumps(payload.__dict__, separators=(",", ":")).encode()
    signature = _get_private_key().sign(payload_bytes)
    return f"{_b64encode(payload_bytes)}.{_b64encode(signature)}"


def verify_hospital_qr(token: str) -> HospitalQrPayload:
    """Signature + expiry only — jti replay must additionally be checked by
    the caller against the DB (a pure function here can't see prior state)."""
    try:
        payload_b64, sig_b64 = token.split(".", 1)
        payload_bytes = _b64decode(payload_b64)
        signature = _b64decode(sig_b64)
    except Exception as exc:
        raise QrVerificationError("malformed_token") from exc

    public_key = _get_private_key().public_key()
    try:
        public_key.verify(signature, payload_bytes)
    except InvalidSignature as exc:
        raise QrVerificationError("invalid_signature") from exc

    data = json.loads(payload_bytes)
    payload = HospitalQrPayload(**data)

    if int(time.time()) > payload.expires_at:
        raise QrVerificationError("expired")

    return payload
