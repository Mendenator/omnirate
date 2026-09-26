"""Moderation worker (P1-06 queue/DLQ infra + P1-07 PII stage).

arq handles retry/backoff internally up to `max_tries`; this module adds a
dead-letter queue so a job that exhausts retries is captured for a human
instead of silently dropped (DoD: no silent data loss in a pipeline that
touches PII).
"""

import json
import uuid
from typing import Any

from arq.connections import RedisSettings

from app.core.config import get_settings
from app.db.session import async_session_factory
from app.domain.audit import append_audit_log
from app.domain.defamation import check_strict_defamation
from app.domain.models import Entity, Review
from app.domain.moderation import PiiFinding, redact_pii

DLQ_KEY = "moderation:dlq"
# Its own queue (not arq's default "arq:queue", which the indexer worker polls):
# two workers with different `functions` sharing one queue would each grab jobs
# they can't run. Used by both the enqueue site (api/v1/reviews.py) and this
# worker's WorkerSettings so the two can't drift apart.
MODERATION_QUEUE_NAME = "arq:queue:moderation"

# strict_defamation (P3-04) applies only to political-branch entities — the
# heightened bar for unsourced criminal allegations isn't appropriate for a
# restaurant review.
STRICT_DEFAMATION_BRANCH = "tur-alba"


async def moderate_review(ctx: dict[str, Any], review_id: str) -> dict[str, Any]:
    """Idempotent: re-running on an already-clean body is a no-op (redact_pii
    on text with no PII returns the input unchanged, and a review already
    blocked stays blocked), so at-least-once delivery from arq's retry
    semantics can't double-redact or un-block anything.
    """
    async with async_session_factory() as db:
        review = await db.get(Review, uuid.UUID(review_id))
        if review is None:
            return {"status": "skipped", "reason": "review deleted before moderation ran"}

        entity = await db.get(Entity, review.entity_id)
        if entity is not None and entity.branch_slug == STRICT_DEFAMATION_BRANCH and review.body:
            defamation_check = check_strict_defamation(review.body)
            if defamation_check.is_blocked:
                review.is_blocked = True
                review.blocked_reason = defamation_check.reason
                await append_audit_log(
                    db,
                    actor_id=None,
                    action="moderation.strict_defamation_block",
                    target_type="review",
                    target_id=review_id,
                    payload={"reason": defamation_check.reason},
                )
                await db.commit()
                return {"status": "blocked", "reason": defamation_check.reason}

        findings: list[PiiFinding] = []
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


async def on_job_failed_permanently(ctx: dict[str, Any], review_id: str, error: str) -> None:
    """Called by app/workers/queue.py's retry wrapper once max_tries is exhausted."""
    redis = ctx["redis"]
    await redis.rpush(DLQ_KEY, json.dumps({"review_id": review_id, "error": error}))


async def startup(ctx: dict[str, Any]) -> None:
    pass


class WorkerSettings:
    functions = [moderate_review]
    queue_name = MODERATION_QUEUE_NAME
    on_startup = startup
    # Must be a plain RedisSettings instance, not a method — see
    # app/workers/indexer.py's WorkerSettings for why.
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)

    # arq built-in retry: a job that raises is retried up to max_tries with
    # backoff; job.info() is inspected by infra/observability alerts.yml's
    # planned DlqDepthHigh rule (added alongside the DLQ queue in prod).
    max_tries = 5
