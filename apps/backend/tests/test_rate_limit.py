from unittest.mock import patch

from app.core.rate_limit import ROUTE_LIMITS_PER_MINUTE


async def test_requests_under_limit_pass_through(client):
    for _ in range(5):
        resp = await client.get("/healthz")
        assert resp.status_code == 200


async def test_requests_over_limit_get_429(client):
    with patch.dict(ROUTE_LIMITS_PER_MINUTE, {"/healthz": 3}):
        statuses = [(await client.get("/healthz")).status_code for _ in range(5)]

    assert statuses[:3] == [200, 200, 200]
    assert 429 in statuses[3:]
