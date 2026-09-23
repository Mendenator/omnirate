import uuid

RESTORAN_SCHEMA = {"type": "object", "properties": {}}


async def _publish_schema(client):
    resp = await client.post(
        "/api/v1/schemas",
        json={
            "category_slug": "emnelge",
            "version": 1,
            "json_schema": RESTORAN_SCHEMA,
            "search_config": {},
            "display_config": {"sections": ["summary"]},
        },
    )
    assert resp.status_code == 201


async def _create_entity(client, ttd="TTD-999"):
    resp = await client.post(
        "/api/v1/entities",
        json={
            "branch_slug": "emnelge",
            "category_slug": "emnelge",
            "schema_version": 1,
            "name": "Улсын эмнэлэг",
            "ttd": ttd,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_issue_qr_requires_ownership(client):
    await _publish_schema(client)
    entity = await _create_entity(client)

    resp = await client.post(f"/api/v1/entities/{entity['id']}/hospital-qr")
    assert resp.status_code == 403


async def test_issue_qr_unknown_entity_is_404(client):
    resp = await client.post(f"/api/v1/entities/{uuid.uuid4()}/hospital-qr")
    assert resp.status_code == 404


async def test_owner_can_issue_and_verify_qr(client):
    await _publish_schema(client)
    entity = await _create_entity(client, ttd="TTD-999")

    claim = await client.post(f"/api/v1/entities/{entity['id']}/claim", json={"ttd": "TTD-999"})
    assert claim.status_code == 201

    issued = await client.post(f"/api/v1/entities/{entity['id']}/hospital-qr")
    assert issued.status_code == 201
    body = issued.json()
    assert body["token"]
    assert body["pdf_base64"]

    verified = await client.post("/api/v1/hospital-qr/verify", json={"token": body["token"]})
    assert verified.status_code == 200
    assert verified.json()["status"] == "verified"


async def test_replayed_qr_token_is_rejected(client):
    await _publish_schema(client)
    entity = await _create_entity(client, ttd="TTD-888")
    await client.post(f"/api/v1/entities/{entity['id']}/claim", json={"ttd": "TTD-888"})
    issued = await client.post(f"/api/v1/entities/{entity['id']}/hospital-qr")
    token = issued.json()["token"]

    first = await client.post("/api/v1/hospital-qr/verify", json={"token": token})
    assert first.status_code == 200
    second = await client.post("/api/v1/hospital-qr/verify", json={"token": token})
    assert second.status_code == 422
    assert second.json()["detail"]["reason_code"] == "jti_replayed_or_unknown"


async def test_malformed_qr_token_is_rejected(client):
    resp = await client.post("/api/v1/hospital-qr/verify", json={"token": "not-a-real-token"})
    assert resp.status_code == 422
