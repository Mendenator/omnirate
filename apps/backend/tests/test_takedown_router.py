import uuid


async def test_create_takedown_as_user(client):
    resp = await client.post(
        "/api/v1/takedowns",
        json={"target_type": "review", "target_id": str(uuid.uuid4()), "reason": "defamatory content"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "open"
    assert body["sla_deadline"]


async def test_create_law_enforcement_request_requires_case_reference(client):
    resp = await client.post(
        "/api/v1/law-enforcement-requests",
        json={
            "target_type": "review",
            "target_id": str(uuid.uuid4()),
            "reason": "court order",
            "case_reference": "CASE-2026-001",
        },
    )
    assert resp.status_code == 201


async def test_resolve_unknown_takedown_is_404(client):
    resp = await client.post(f"/api/v1/takedowns/{uuid.uuid4()}/resolve", json={"status": "resolved"})
    assert resp.status_code == 404


async def test_resolve_takedown(client):
    created = await client.post(
        "/api/v1/takedowns",
        json={"target_type": "entity", "target_id": str(uuid.uuid4()), "reason": "fake listing"},
    )
    takedown_id = created.json()["id"]

    resolved = await client.post(f"/api/v1/takedowns/{takedown_id}/resolve", json={"status": "resolved"})
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"


async def test_resolving_an_already_resolved_takedown_is_409(client):
    created = await client.post(
        "/api/v1/takedowns",
        json={"target_type": "entity", "target_id": str(uuid.uuid4()), "reason": "fake listing"},
    )
    takedown_id = created.json()["id"]
    await client.post(f"/api/v1/takedowns/{takedown_id}/resolve", json={"status": "resolved"})

    again = await client.post(f"/api/v1/takedowns/{takedown_id}/resolve", json={"status": "rejected"})
    assert again.status_code == 409
