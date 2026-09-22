"""Moderation worker (P1-06 queue/DLQ infra + P1-07 PII stage).

arq handles retry/backoff internally up to `max_tries`; this module adds a
dead-letter queue so a job that exhausts retries is captured for a human
instead of silently dropped (DoD: no silent data loss in a pipeline that
touches PII).
"""

import json
import uuid

from arq.connections import RedisSettings

from app.core.config import get_settings
from app.db.session import async_session_factory
from app.domain.audit import append_audit_log
from app.domain.models import Review
from app.domain.moderation import redact_pii

DLQ_KEY = "moderation:dlq"
MODERATION_QUEUE_NAME = "moderation"


async def moderate_review(ctx, review_id: str) -> dict:
    """Idempotent: re-running on an already-clean body is a no-op (redact_pii
    on text with no PII returns the input unchanged), so at-least-once
    delivery from arq's retry semantics can't double-redact.
    """
    async with async_session_factory() as db:
        review = await db.get(Review, uuid.UUID(review_id))
        if review is None:
            return {"status": "skipped", "reason": "review deleted before moderation ran"}

        findings = []
        if review.body:
            redacted, findings = redact_pii(review.body)
            review.body = redacted

        await append_audit_log(
            db,
            actor_id=None,
            action="moderation.pii_scan",
            target_type="review",
            target_id=review_id,
            payload={"findings": [f.kind for f in findings]},
        )
        await db.commit()
        return {"status": "ok", "pii_findings": len(findings)}


async def on_job_failed_permanently(ctx, review_id: str, error: str) -> None:
    """Called by app/workers/queue.py's retry wrapper once max_tries is exhausted."""
    redis = ctx["redis"]
    await redis.rpush(DLQ_KEY, json.dumps({"review_id": review_id, "error": error}))


async def startup(ctx):
    pass


class WorkerSettings:
    functions = [moderate_review]
    on_startup = startup

    @staticmethod
    def redis_settings() -> RedisSettings:
        return RedisSettings.from_dsn(get_settings().redis_url)

    # arq built-in retry: a job that raises is retried up to max_tries with
    # backoff; job.info() is inspected by infra/observability alerts.yml's
    # planned DlqDepthHigh rule (added alongside the DLQ queue in prod).
    max_tries = 5
