from unittest.mock import AsyncMock, patch

REDIRECT_URI = "https://app.omnirate.mn/callback"


async def _dan_start(client):
    resp = await client.get("/api/v1/auth/dan/start", params={"redirect_uri": REDIRECT_URI})
    assert resp.status_code == 200
    return resp.json()["state"]


async def test_dan_start_returns_authorize_url_and_state(client):
    resp = await client.get("/api/v1/auth/dan/start", params={"redirect_uri": REDIRECT_URI})
    assert resp.status_code == 200
    body = resp.json()
    assert body["state"]
    assert REDIRECT_URI in body["authorize_url"]


async def test_dan_callback_unknown_state_rejected(client):
    resp = await client.post(
        "/api/v1/auth/dan/callback",
        json={"code": "abc", "state": "never-issued", "redirect_uri": REDIRECT_URI},
    )
    assert resp.status_code == 400


async def test_dan_callback_creates_new_user_and_issues_token(client):
    state = await _dan_start(client)

    with patch(
        "app.api.v1.auth.dan_auth.exchange_code_for_dan_identity",
        AsyncMock(return_value={"rd": "AB12345678", "name": "Bat"}),
    ):
        resp = await client.post(
            "/api/v1/auth/dan/callback", json={"code": "code-1", "state": state, "redirect_uri": REDIRECT_URI}
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["poe_level"] == "L2"
    assert body["access_token"]


async def test_dan_callback_reuses_existing_user_by_rd_hash(client):
    identity = {"rd": "AB99999999", "name": "Sara"}

    state1 = await _dan_start(client)
    with patch("app.api.v1.auth.dan_auth.exchange_code_for_dan_identity", AsyncMock(return_value=identity)):
        first = await client.post(
            "/api/v1/auth/dan/callback", json={"code": "code-1", "state": state1, "redirect_uri": REDIRECT_URI}
        )
    assert first.status_code == 200

    state2 = await _dan_start(client)
    with patch("app.api.v1.auth.dan_auth.exchange_code_for_dan_identity", AsyncMock(return_value=identity)):
        second = await client.post(
            "/api/v1/auth/dan/callback", json={"code": "code-2", "state": state2, "redirect_uri": REDIRECT_URI}
        )
    assert second.status_code == 200
    # Same underlying rd_hash -> same user, but each callback issues a fresh token.
    assert first.json()["access_token"] != second.json()["access_token"]


async def test_otp_verify_issues_l1_token(client):
    resp = await client.post("/api/v1/auth/otp/verify", json={"phone": "99001122", "otp_code": "123456"})
    assert resp.status_code == 200
    assert resp.json()["poe_level"] == "L1"


async def test_otp_verify_reuses_existing_user_for_same_phone(client):
    first = await client.post("/api/v1/auth/otp/verify", json={"phone": "88112233", "otp_code": "111111"})
    second = await client.post("/api/v1/auth/otp/verify", json={"phone": "88112233", "otp_code": "222222"})
    assert first.status_code == 200
    assert second.status_code == 200
