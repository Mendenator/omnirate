"""Hash-chained audit log helper, shared by moderation, claims, takedowns, etc.

Each row's `row_hash` covers its own fields plus the previous row's hash, so
tampering with any historical row breaks the chain from that point forward —
the acceptance criterion P3-05 calls "Audit log-ийн мөрийг өөрчлөх оролдлого
илрэх 100%" is really just "is this chain still valid," checked by
`verify_chain` below.
"""

import hashlib
import json
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import AuditLog


def _row_hash(*, prev_hash: str | None, action: str, target_type: str, target_id: str, payload: dict) -> str:
    canonical = json.dumps(
        {"prev_hash": prev_hash, "action": action, "target_type": target_type, "target_id": target_id, "payload": payload},
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


async def append_audit_log(
    db: AsyncSession, *, actor_id: uuid.UUID | None, action: str, target_type: str, target_id: str, payload: dict
) -> AuditLog:
    last = await db.scalar(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(1))
    prev_hash = last.row_hash if last else None

    row_hash = _row_hash(prev_hash=prev_hash, action=action, target_type=target_type, target_id=target_id, payload=payload)
    entry = AuditLog(
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        payload=payload,
        prev_hash=prev_hash,
        row_hash=row_hash,
    )
    db.add(entry)
    return entry


def verify_chain(entries: list[AuditLog]) -> bool:
    """`entries` must be ordered oldest-first. Returns False at the first break."""
    prev_hash: str | None = None
    for entry in entries:
        if entry.prev_hash != prev_hash:
            return False
        expected = _row_hash(
            prev_hash=prev_hash,
            action=entry.action,
            target_type=entry.target_type,
            target_id=entry.target_id,
            payload=entry.payload,
        )
        if expected != entry.row_hash:
            return False
        prev_hash = entry.row_hash
    return True
