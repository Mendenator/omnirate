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
