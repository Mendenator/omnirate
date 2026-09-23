import uuid

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


async def _create_entity(client, ttd="TTD-123"):
    resp = await client.post(
        "/api/v1/entities",
        json={
            "branch_slug": "hool-zoog",
            "category_slug": "restoran",
            "schema_version": 1,
            "name": "Хаан буудал",
            "ttd": ttd,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_claim_with_mismatched_ttd_is_rejected(client):
    await _publish_schema(client)
    entity = await _create_entity(client, ttd="TTD-123")

    resp = await client.post(f"/api/v1/entities/{entity['id']}/claim", json={"ttd": "TTD-WRONG"})
    assert resp.status_code == 422


async def test_claim_with_matching_ttd_succeeds(client):
    await _publish_schema(client)
    entity = await _create_entity(client, ttd="TTD-123")

    resp = await client.post(f"/api/v1/entities/{entity['id']}/claim", json={"ttd": "TTD-123"})
    assert resp.status_code == 201


async def test_double_claim_is_409(client):
    await _publish_schema(client)
    entity = await _create_entity(client, ttd="TTD-123")

    first = await client.post(f"/api/v1/entities/{entity['id']}/claim", json={"ttd": "TTD-123"})
    assert first.status_code == 201
    second = await client.post(f"/api/v1/entities/{entity['id']}/claim", json={"ttd": "TTD-123"})
    assert second.status_code == 409


async def test_create_complaint(client):
    await _publish_schema(client)
    entity = await _create_entity(client)

    resp = await client.post(
        "/api/v1/complaints",
        json={"target_type": "entity", "target_id": entity["id"], "reason": "fake_entity"},
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "open"


async def _create_review(client, entity_id):
    resp = await client.post(
        "/api/v1/reviews",
        json={"entity_id": entity_id, "overall_score": 3.0, "criteria_scores": {}, "body": "OK"},
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_reply_without_claiming_is_403(client):
    await _publish_schema(client)
    entity = await _create_entity(client)
    review = await _create_review(client, entity["id"])

    resp = await client.post(
        f"/api/v1/entities/{entity['id']}/reviews/{review['id']}/reply", json={"body": "Баярлалаа"}
    )
    assert resp.status_code == 403


async def test_owner_can_reply_to_review_on_their_entity(client):
    await _publish_schema(client)
    entity = await _create_entity(client)
    review = await _create_review(client, entity["id"])

    claim = await client.post(f"/api/v1/entities/{entity['id']}/claim", json={"ttd": "TTD-123"})
    assert claim.status_code == 201

    resp = await client.post(
        f"/api/v1/entities/{entity['id']}/reviews/{review['id']}/reply", json={"body": "Баярлалаа"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "replied"


async def test_reply_to_review_on_a_different_entity_is_404(client):
    await _publish_schema(client)
    entity = await _create_entity(client, ttd="TTD-123")
    other_entity = await _create_entity(client, ttd="TTD-456")
    review = await _create_review(client, entity["id"])

    claim = await client.post(f"/api/v1/entities/{other_entity['id']}/claim", json={"ttd": "TTD-456"})
    assert claim.status_code == 201

    resp = await client.post(
        f"/api/v1/entities/{other_entity['id']}/reviews/{review['id']}/reply", json={"body": "Баярлалаа"}
    )
    assert resp.status_code == 404


async def test_claim_unknown_entity_is_404(client):
    resp = await client.post(f"/api/v1/entities/{uuid.uuid4()}/claim", json={"ttd": "TTD-123"})
    assert resp.status_code == 404
