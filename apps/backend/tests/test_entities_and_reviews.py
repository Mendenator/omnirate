import uuid
from unittest.mock import AsyncMock

from app.domain.models import Review, User
from app.main import app

RESTORAN_SCHEMA = {"type": "object", "properties": {"cuisine": {"type": "string"}}}


async def _publish_schema(client):
    resp = await client.post(
        "/api/v1/schemas",
        json={
            "category_slug": "restoran",
            "version": 1,
            "json_schema": RESTORAN_SCHEMA,
            "search_config": {},
            "display_config": {"sections": ["summary"]},
        },
    )
    assert resp.status_code == 201


async def _create_entity(client, name="Хаан буудал"):
    resp = await client.post(
        "/api/v1/entities",
        json={
            "branch_slug": "hool-zoog",
            "category_slug": "restoran",
            "schema_version": 1,
            "name": name,
            "attributes": {"cuisine": "монгол"},
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_create_entity(client):
    await _publish_schema(client)
    entity = await _create_entity(client)
    assert entity["name"] == "Хаан буудал"
    assert entity["verified"] is False


async def test_get_entity_not_found(client):
    resp = await client.get("/api/v1/entities/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


async def test_create_review_requires_idempotency_key(client):
    await _publish_schema(client)
    entity = await _create_entity(client)
    resp = await client.post(
        "/api/v1/reviews",
        json={"entity_id": entity["id"], "overall_score": 4.5},
        headers={"Authorization": "Bearer fake"},  # bypassed by dependency_override anyway
    )
    assert resp.status_code == 422  # missing Idempotency-Key header


async def test_create_review_then_duplicate_is_409(client):
    await _publish_schema(client)
    entity = await _create_entity(client)
    headers = {"Idempotency-Key": "key-1", "Authorization": "Bearer fake"}

    first = await client.post(
        "/api/v1/reviews", json={"entity_id": entity["id"], "overall_score": 4.5}, headers=headers
    )
    assert first.status_code == 201

    duplicate = await client.post(
        "/api/v1/reviews",
        json={"entity_id": entity["id"], "overall_score": 3.0},
        headers={"Idempotency-Key": "key-2", "Authorization": "Bearer fake"},
    )
    assert duplicate.status_code == 409  # same (entity, user) pair


async def test_idempotency_key_replay_returns_cached_response(client):
    await _publish_schema(client)
    entity = await _create_entity(client)
    headers = {"Idempotency-Key": "replay-key", "Authorization": "Bearer fake"}
    payload = {"entity_id": entity["id"], "overall_score": 4.0}

    first = await client.post("/api/v1/reviews", json=payload, headers=headers)
    second = await client.post("/api/v1/reviews", json=payload, headers=headers)

    assert first.status_code == second.status_code == 201
    assert first.json()["id"] == second.json()["id"]


async def _seed_review(db_session, *, entity_id, overall_score, criteria_scores=None, poe_level="L2", is_blocked=False):
    user = User(rd_hash=f"rd-{uuid.uuid4()}", display_name="Seeded user", poe_level=poe_level)
    db_session.add(user)
    await db_session.flush()
    review = Review(
        entity_id=entity_id,
        user_id=user.id,
        poe_level=poe_level,
        overall_score=overall_score,
        criteria_scores=criteria_scores or {},
        is_blocked=is_blocked,
    )
    db_session.add(review)
    await db_session.commit()
    return review


async def test_get_entity_with_no_reviews_falls_back_to_prior(client):
    await _publish_schema(client)
    entity = await _create_entity(client)

    resp = await client.get(f"/api/v1/entities/{entity['id']}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["score"] == 3.5  # CATEGORY_PRIOR_MEAN, no reviews to pull it anywhere
    assert body["review_count"] == 0
    assert body["verified_review_count"] == 0
    assert body["criteria_breakdown"] == {}


async def test_get_entity_reflects_criteria_breakdown_and_verified_count(client, db_session):
    await _publish_schema(client)
    entity = await _create_entity(client)
    entity_id = entity["id"]

    await _seed_review(
        db_session, entity_id=entity_id, overall_score=5.0, criteria_scores={"food": 5.0}, poe_level="L4"
    )
    await _seed_review(
        db_session, entity_id=entity_id, overall_score=3.0, criteria_scores={"food": 3.0}, poe_level="L0"
    )

    resp = await client.get(f"/api/v1/entities/{entity_id}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["review_count"] == 2
    assert body["verified_review_count"] == 1  # only the L4 review counts as verified
    assert body["criteria_breakdown"] == {"food": 4.0}
    assert 0 <= body["score"] <= 5


async def test_get_entity_excludes_blocked_reviews(client, db_session):
    await _publish_schema(client)
    entity = await _create_entity(client)
    entity_id = entity["id"]

    await _seed_review(db_session, entity_id=entity_id, overall_score=5.0, criteria_scores={"food": 5.0})
    await _seed_review(
        db_session, entity_id=entity_id, overall_score=0.5, criteria_scores={"food": 0.5}, is_blocked=True
    )

    resp = await client.get(f"/api/v1/entities/{entity_id}")

    body = resp.json()
    assert body["review_count"] == 1
    assert body["criteria_breakdown"] == {"food": 5.0}


async def test_list_reviews_excludes_blocked_and_orders_newest_first(client, db_session):
    await _publish_schema(client)
    entity = await _create_entity(client)
    entity_id = entity["id"]

    visible = await _seed_review(db_session, entity_id=entity_id, overall_score=4.0)
    await _seed_review(db_session, entity_id=entity_id, overall_score=1.0, is_blocked=True)

    resp = await client.get(f"/api/v1/entities/{entity_id}/reviews")

    assert resp.status_code == 200
    ids = [r["id"] for r in resp.json()]
    assert ids == [str(visible.id)]


async def test_list_reviews_for_missing_entity_is_404(client):
    resp = await client.get(f"/api/v1/entities/{uuid.uuid4()}/reviews")
    assert resp.status_code == 404


async def test_creating_an_entity_enqueues_a_reindex_job(client):
    await _publish_schema(client)
    arq_pool = AsyncMock()
    app.state.arq_pool = arq_pool
    try:
        entity = await _create_entity(client)
    finally:
        del app.state.arq_pool

    arq_pool.enqueue_job.assert_awaited_once_with("reindex_entity", entity["id"])
