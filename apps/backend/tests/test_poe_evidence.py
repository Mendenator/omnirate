import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

from app.core.e_barimt import EBarimtReceiptData

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


async def _create_entity(client, *, ttd="TTD-123", lat=None, lon=None):
    resp = await client.post(
        "/api/v1/entities",
        json={
            "branch_slug": "hool-zoog",
            "category_slug": "restoran",
            "schema_version": 1,
            "name": "Хаан буудал",
            "ttd": ttd,
            "lat": lat,
            "lon": lon,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _create_review(client, entity_id, *, idempotency_key=None):
    resp = await client.post(
        "/api/v1/reviews",
        json={"entity_id": entity_id, "overall_score": 4.5, "criteria_scores": {}, "body": "Сайн байсан"},
        headers={"Idempotency-Key": idempotency_key or str(uuid.uuid4())},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_e_barimt_evidence_review_not_found(client):
    resp = await client.post(f"/api/v1/reviews/{uuid.uuid4()}/evidence/e-barimt", json={"qr_payload": "whatever"})
    assert resp.status_code == 404


async def test_e_barimt_ttd_mismatch_rejected(client):
    await _publish_schema(client)
    entity = await _create_entity(client, ttd="TTD-123")
    review = await _create_review(client, entity["id"])

    fake_receipt = EBarimtReceiptData(ddtd="D-1", ttd="TTD-OTHER", amount=1000, purchased_at=datetime.now(UTC))
    with patch("app.api.v1.poe_evidence.e_barimt.verify_qr_payload", AsyncMock(return_value=fake_receipt)):
        resp = await client.post(f"/api/v1/reviews/{review['id']}/evidence/e-barimt", json={"qr_payload": "qr"})

    assert resp.status_code == 422
    assert resp.json()["detail"]["reason_code"] == "ttd_mismatch"


async def test_e_barimt_receipt_too_old_rejected(client):
    await _publish_schema(client)
    entity = await _create_entity(client, ttd="TTD-123")
    review = await _create_review(client, entity["id"])

    fake_receipt = EBarimtReceiptData(
        ddtd="D-2", ttd="TTD-123", amount=1000, purchased_at=datetime.now(UTC) - timedelta(days=91)
    )
    with patch("app.api.v1.poe_evidence.e_barimt.verify_qr_payload", AsyncMock(return_value=fake_receipt)):
        resp = await client.post(f"/api/v1/reviews/{review['id']}/evidence/e-barimt", json={"qr_payload": "qr"})

    assert resp.status_code == 422
    assert resp.json()["detail"]["reason_code"] == "receipt_too_old"


async def test_e_barimt_success_upgrades_poe_level_to_l4(client):
    await _publish_schema(client)
    entity = await _create_entity(client, ttd="TTD-123")
    review = await _create_review(client, entity["id"])

    fake_receipt = EBarimtReceiptData(ddtd="D-3", ttd="TTD-123", amount=1000, purchased_at=datetime.now(UTC))
    with patch("app.api.v1.poe_evidence.e_barimt.verify_qr_payload", AsyncMock(return_value=fake_receipt)):
        resp = await client.post(f"/api/v1/reviews/{review['id']}/evidence/e-barimt", json={"qr_payload": "qr"})

    assert resp.status_code == 201
    assert resp.json()["poe_level"] == "L4"


async def test_e_barimt_replayed_ddtd_is_409(client):
    await _publish_schema(client)
    # Two separate entities: the same (fake) user can only review a given
    # entity once (unique (entity_id, user_id)), so replaying a ddtd across
    # two reviews needs two distinct entities, not two reviews of one.
    entity_a = await _create_entity(client, ttd="TTD-123")
    entity_b = await _create_entity(client, ttd="TTD-123")
    review_a = await _create_review(client, entity_a["id"])
    review_b = await _create_review(client, entity_b["id"])

    fake_receipt = EBarimtReceiptData(ddtd="D-SHARED", ttd="TTD-123", amount=1000, purchased_at=datetime.now(UTC))
    with patch("app.api.v1.poe_evidence.e_barimt.verify_qr_payload", AsyncMock(return_value=fake_receipt)):
        first = await client.post(f"/api/v1/reviews/{review_a['id']}/evidence/e-barimt", json={"qr_payload": "qr"})
        assert first.status_code == 201
        second = await client.post(f"/api/v1/reviews/{review_b['id']}/evidence/e-barimt", json={"qr_payload": "qr"})

    assert second.status_code == 409
    assert second.json()["detail"]["reason_code"] == "ddtd_already_used"


async def test_gps_evidence_review_not_found(client):
    resp = await client.post(f"/api/v1/reviews/{uuid.uuid4()}/evidence/gps", json={"pings": []})
    assert resp.status_code == 404


async def test_gps_evidence_entity_without_geofence_center_rejected(client):
    await _publish_schema(client)
    entity = await _create_entity(client, lat=None, lon=None)
    review = await _create_review(client, entity["id"])

    resp = await client.post(f"/api/v1/reviews/{review['id']}/evidence/gps", json={"pings": []})
    assert resp.status_code == 422
    assert resp.json()["detail"]["reason_code"] == "no_entity_location"


async def _ping(lat, lon, seconds_ago, *, mock=False, accuracy=5.0):
    return {
        "lat": lat,
        "lon": lon,
        "accuracy_m": accuracy,
        "is_mock_provider_flag": mock,
        "recorded_at": (datetime.now(UTC) - timedelta(seconds=seconds_ago)).isoformat(),
    }


async def test_gps_evidence_mock_location_rejected(client):
    await _publish_schema(client)
    entity = await _create_entity(client, lat=47.9, lon=106.9)
    review = await _create_review(client, entity["id"])

    pings = [await _ping(47.9, 106.9, 10, mock=True)]
    resp = await client.post(f"/api/v1/reviews/{review['id']}/evidence/gps", json={"pings": pings})

    assert resp.status_code == 422
    assert resp.json()["detail"]["reason_code"] == "mock_location_detected"


async def test_gps_evidence_insufficient_dwell_rejected(client):
    await _publish_schema(client)
    entity = await _create_entity(client, lat=47.9, lon=106.9)
    review = await _create_review(client, entity["id"])

    pings = [await _ping(47.9, 106.9, 10), await _ping(47.9, 106.9, 5)]
    resp = await client.post(f"/api/v1/reviews/{review['id']}/evidence/gps", json={"pings": pings})

    assert resp.status_code == 422
    assert resp.json()["detail"]["reason_code"] == "insufficient_dwell_time"


async def test_gps_evidence_success_upgrades_poe_level_to_l2(client):
    await _publish_schema(client)
    entity = await _create_entity(client, lat=47.9, lon=106.9)
    review = await _create_review(client, entity["id"])

    pings = [await _ping(47.9, 106.9, 400), await _ping(47.9, 106.9, 10)]
    resp = await client.post(f"/api/v1/reviews/{review['id']}/evidence/gps", json={"pings": pings})

    assert resp.status_code == 201
    body = resp.json()
    assert body["poe_level"] == "L2"
    assert body["dwell_seconds"] >= 300
