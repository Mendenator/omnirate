import uuid
from unittest.mock import AsyncMock

from app.main import app
from app.workers.moderation import MODERATION_QUEUE_NAME

RESTORAN_SCHEMA = {"type": "object", "properties": {}}


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


async def _create_entity(client):
    resp = await client.post(
        "/api/v1/entities",
        json={
            "branch_slug": "hool-zoog",
            "category_slug": "restoran",
            "schema_version": 1,
            "name": "Хаан буудал",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_create_review(client):
    await _publish_schema(client)
    entity = await _create_entity(client)

    resp = await client.post(
        "/api/v1/reviews",
        json={"entity_id": entity["id"], "overall_score": 4.0, "criteria_scores": {"food": 4.5}, "body": "Сайн"},
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )
    assert resp.status_code == 201
    assert resp.json()["overall_score"] == 4.0


async def test_repeating_the_same_idempotency_key_returns_the_cached_response(client):
    await _publish_schema(client)
    entity = await _create_entity(client)
    key = str(uuid.uuid4())
    payload = {"entity_id": entity["id"], "overall_score": 3.5, "criteria_scores": {}, "body": "OK"}

    first = await client.post("/api/v1/reviews", json=payload, headers={"Idempotency-Key": key})
    second = await client.post("/api/v1/reviews", json=payload, headers={"Idempotency-Key": key})

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]


async def test_duplicate_review_without_matching_idempotency_key_is_409(client):
    await _publish_schema(client)
    entity = await _create_entity(client)
    payload = {"entity_id": entity["id"], "overall_score": 3.5, "criteria_scores": {}, "body": "OK"}

    first = await client.post("/api/v1/reviews", json=payload, headers={"Idempotency-Key": str(uuid.uuid4())})
    assert first.status_code == 201

    second = await client.post("/api/v1/reviews", json=payload, headers={"Idempotency-Key": str(uuid.uuid4())})
    assert second.status_code == 409


async def test_repeating_the_idempotency_key_of_a_failed_request_returns_the_cached_error(client):
    await _publish_schema(client)
    entity = await _create_entity(client)
    payload = {"entity_id": entity["id"], "overall_score": 3.5, "criteria_scores": {}, "body": "OK"}

    await client.post("/api/v1/reviews", json=payload, headers={"Idempotency-Key": str(uuid.uuid4())})
    failing_key = str(uuid.uuid4())
    first_fail = await client.post("/api/v1/reviews", json=payload, headers={"Idempotency-Key": failing_key})
    assert first_fail.status_code == 409

    replay = await client.post("/api/v1/reviews", json=payload, headers={"Idempotency-Key": failing_key})
    assert replay.status_code == 409
    assert replay.json() == first_fail.json()


async def test_creating_a_review_enqueues_moderation_and_reindex_jobs(client):
    await _publish_schema(client)
    entity = await _create_entity(client)
    arq_pool = AsyncMock()
    app.state.arq_pool = arq_pool
    try:
        resp = await client.post(
            "/api/v1/reviews",
            json={"entity_id": entity["id"], "overall_score": 4.0},
            headers={"Idempotency-Key": str(uuid.uuid4())},
        )
        assert resp.status_code == 201
        review_id = resp.json()["id"]
    finally:
        del app.state.arq_pool

    calls = {call.args[0]: call for call in arq_pool.enqueue_job.await_args_list}
    assert calls["moderate_review"].args[1] == review_id
    assert calls["moderate_review"].kwargs["_queue_name"] == MODERATION_QUEUE_NAME
    assert calls["reindex_entity"].args[1] == entity["id"]
    # reindex_entity deliberately has no _queue_name override — the indexer
    # worker's WorkerSettings never sets one, so it polls arq's default
    # queue, and an invented name here would just leave the job unread.
    assert "_queue_name" not in calls["reindex_entity"].kwargs
