"""CDC indexer worker (S-03 / K13): Debezium emits row-change events for `entities`
and `reviews` onto the `omnirate.cdc.entities` Redis stream (via the Debezium
Kafka-Connect → Redis bridge configured in infra/terraform/modules/opensearch);
this arq worker consumes them and upserts the corresponding OpenSearch document.

K13 target: publish → searchable within 60s p95. The two hops that matter for
that budget are Debezium's poll interval (infra/terraform, default 500ms) and
this worker's queue latency — both are tracked as separate OTel spans so a
budget breach can be attributed to a stage.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from arq import cron
from arq.connections import RedisSettings
from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import async_session_factory
from app.domain.models import Entity, Review
from app.domain.poe import counts_as_verified
from app.domain.scoring import ScoredReview, compute_bayesian_trimmed_score
from app.search.client import ENTITIES_ALIAS, ensure_entities_index, get_opensearch_client
from app.search.mongolian_text import build_name_folded

CATEGORY_PRIOR_MEAN = 3.5  # placeholder until S-08's gold set gives a real per-category prior
CATEGORY_PRIOR_CONFIDENCE = 10.0


async def reindex_entity(ctx: dict[str, Any], entity_id: str) -> None:
    async with async_session_factory() as db:
        entity = await db.get(Entity, uuid.UUID(entity_id))
        if entity is None:
            # Deleted since the CDC event was enqueued — remove from the index.
            await ctx["opensearch"].delete(index=ENTITIES_ALIAS, id=entity_id, ignore=[404])
            return

        reviews = (await db.execute(select(Review).where(Review.entity_id == entity.id))).scalars().all()
        n_verified = sum(1 for r in reviews if counts_as_verified(r.poe_level))
        score = compute_bayesian_trimmed_score(
            [
                ScoredReview(
                    overall_score=float(r.overall_score), poe_level=r.poe_level, fraud_score=float(r.fraud_score)
                )
                for r in reviews
            ],
            prior_mean=CATEGORY_PRIOR_MEAN,
            prior_confidence=CATEGORY_PRIOR_CONFIDENCE,
        )

        doc = {
            "entity_id": str(entity.id),
            "branch_slug": entity.branch_slug,
            "category_slug": entity.category_slug,
            "name": entity.name,
            "name_folded": build_name_folded(entity.name),
            "name_translit": entity.name,  # translit is query-side (S-05); indexed name stays canonical Cyrillic
            "name_edge": entity.name,
            "location_slug": entity.location_slug,
            "location": {"lat": float(entity.lat), "lon": float(entity.lon)} if entity.lat and entity.lon else None,
            "attributes": entity.attributes,
            "score": score,
            "n_verified": n_verified,
            "updated_at": datetime.now(UTC).isoformat(),
        }
        await ctx["opensearch"].index(index=ENTITIES_ALIAS, id=str(entity.id), body=doc, refresh=False)


async def startup(ctx: dict[str, Any]) -> None:
    ctx["opensearch"] = get_opensearch_client()
    await ensure_entities_index(ctx["opensearch"])


async def shutdown(ctx: dict[str, Any]) -> None:
    await ctx["opensearch"].close()


async def noop_heartbeat(ctx: dict[str, Any]) -> None:
    """Keeps a metric alive so Grafana can alert on worker liveness, not just queue depth."""
    return None


class WorkerSettings:
    # cron()'s string form resolves via import_string at class-body-eval time
    # (i.e. while this module is still executing top-to-bottom) — referencing
    # noop_heartbeat by string only works because it's defined *above* this
    # class. Defining it after WorkerSettings instead throws ImportError
    # ("does not define a noop_heartbeat attribute"): the module is
    # mid-import, so the name genuinely doesn't exist in its namespace yet.
    functions = [reindex_entity]
    cron_jobs = [cron("app.workers.indexer.noop_heartbeat", minute=set(range(60)))]
    on_startup = startup
    on_shutdown = shutdown
    # arq reads this straight out of the class __dict__ (not via normal
    # attribute access), so it must be a plain RedisSettings instance, not a
    # method — a @staticmethod here hands arq the descriptor object itself
    # and it crashes on `settings.host` (AttributeError: 'staticmethod'
    # object has no attribute 'host'). Same fix applied identically in
    # app/workers/moderation.py, attendance.py, transparency.py, and
    # app/analytics/worker.py — all had this same bug.
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
