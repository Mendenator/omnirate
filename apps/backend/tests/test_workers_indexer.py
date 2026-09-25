import uuid
from unittest.mock import AsyncMock, patch

from app.domain.models import Entity, Review, User
from app.workers.indexer import noop_heartbeat, reindex_entity, shutdown, startup


async def test_reindex_deletes_from_index_when_entity_is_gone(worker_db):
    opensearch = AsyncMock()
    ctx = {"opensearch": opensearch}

    await reindex_entity(ctx, str(uuid.uuid4()))

    opensearch.delete.assert_awaited_once()
    opensearch.index.assert_not_called()


async def test_reindex_upserts_document_for_existing_entity(db_session, worker_db):
    entity = Entity(
        branch_slug="hool-zoog",
        category_slug="restoran",
        schema_version=1,
        name="Хаан буудал",
        lat=47.9,
        lon=106.9,
    )
    db_session.add(entity)
    await db_session.flush()
    user = User(rd_hash=f"rd-{uuid.uuid4()}", display_name="Reviewer", poe_level="L4")
    db_session.add(user)
    await db_session.flush()
    db_session.add(Review(entity_id=entity.id, user_id=user.id, poe_level="L4", overall_score=4.5, fraud_score=0.0))
    await db_session.commit()

    opensearch = AsyncMock()
    ctx = {"opensearch": opensearch}

    await reindex_entity(ctx, str(entity.id))

    opensearch.index.assert_awaited_once()
    _, kwargs = opensearch.index.call_args
    assert kwargs["id"] == str(entity.id)
    assert kwargs["body"]["name"] == "Хаан буудал"
    assert kwargs["body"]["n_verified"] == 1


async def test_reindex_excludes_blocked_reviews_from_score_and_count(db_session, worker_db):
    entity = Entity(branch_slug="hool-zoog", category_slug="restoran", schema_version=1, name="Хаан буудал")
    db_session.add(entity)
    await db_session.flush()
    user = User(rd_hash=f"rd-{uuid.uuid4()}", display_name="Reviewer", poe_level="L4")
    db_session.add(user)
    await db_session.flush()
    db_session.add(
        Review(
            entity_id=entity.id,
            user_id=user.id,
            poe_level="L4",
            overall_score=1.0,
            fraud_score=0.0,
            is_blocked=True,
        )
    )
    await db_session.commit()

    opensearch = AsyncMock()
    await reindex_entity({"opensearch": opensearch}, str(entity.id))

    _, kwargs = opensearch.index.call_args
    assert kwargs["body"]["n_verified"] == 0
    assert kwargs["body"]["score"] == 3.5  # falls back to the prior — the blocked review is excluded entirely


async def test_reindex_handles_entity_with_no_location(db_session, worker_db):
    entity = Entity(branch_slug="hool-zoog", category_slug="restoran", schema_version=1, name="No Location")
    db_session.add(entity)
    await db_session.commit()

    opensearch = AsyncMock()
    await reindex_entity({"opensearch": opensearch}, str(entity.id))

    _, kwargs = opensearch.index.call_args
    assert kwargs["body"]["location"] is None


async def test_startup_initializes_opensearch_client_and_ensures_index():
    fake_client = AsyncMock()
    ctx = {}
    with (
        patch("app.workers.indexer.get_opensearch_client", return_value=fake_client) as get_client,
        patch("app.workers.indexer.ensure_entities_index", AsyncMock()) as ensure_index,
    ):
        await startup(ctx)

    get_client.assert_called_once()
    ensure_index.assert_awaited_once_with(fake_client)
    assert ctx["opensearch"] is fake_client


async def test_shutdown_closes_opensearch_client():
    opensearch = AsyncMock()
    await shutdown({"opensearch": opensearch})
    opensearch.close.assert_awaited_once()


async def test_noop_heartbeat_returns_none():
    assert await noop_heartbeat({}) is None
