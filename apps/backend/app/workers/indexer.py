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

from arq import cron
from arq.connections import RedisSettings
from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import async_session_factory
from app.domain.models import Entity, Review
from app.search.client import ENTITIES_ALIAS, ensure_entities_index, get_opensearch_client


async def reindex_entity(ctx, entity_id: str) -> None:
    async with async_session_factory() as db:
        entity = await db.get(Entity, uuid.UUID(entity_id))
        if entity is None:
            # Deleted since the CDC event was enqueued — remove from the index.
            await ctx["opensearch"].delete(index=ENTITIES_ALIAS, id=entity_id, ignore=[404])
            return

        reviews = (await db.execute(select(Review).where(Review.entity_id == entity.id))).scalars().all()
        n_verified = sum(1 for r in reviews if r.poe_level in ("L2", "L3", "L4"))
        avg_score = sum(float(r.overall_score) for r in reviews) / len(reviews) if reviews else 0.0

        doc = {
            "entity_id": str(entity.id),
            "branch_slug": entity.branch_slug,
            "category_slug": entity.category_slug,
            "name": entity.name,
            "location_slug": entity.location_slug,
            "location": {"lat": float(entity.lat), "lon": float(entity.lon)} if entity.lat and entity.lon else None,
            "attributes": entity.attributes,
            "score": avg_score,
            "n_verified": n_verified,
            "updated_at": datetime.now(UTC).isoformat(),
        }
        await ctx["opensearch"].index(index=ENTITIES_ALIAS, id=str(entity.id), body=doc, refresh=False)


async def startup(ctx):
    ctx["opensearch"] = get_opensearch_client()
    await ensure_entities_index(ctx["opensearch"])


async def shutdown(ctx):
    await ctx["opensearch"].close()


class WorkerSettings:
    functions = [reindex_entity]
    cron_jobs = [cron("app.workers.indexer.noop_heartbeat", minute=set(range(60)))]
    on_startup = startup
    on_shutdown = shutdown

    @staticmethod
    def redis_settings() -> RedisSettings:
        return RedisSettings.from_dsn(get_settings().redis_url)


async def noop_heartbeat(ctx) -> None:
    """Keeps a metric alive so Grafana can alert on worker liveness, not just queue depth."""
    return None
