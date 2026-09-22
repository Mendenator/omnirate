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
