from app.core.security import decode_access_token, hash_rd, issue_access_token


def test_hash_rd_is_deterministic_and_not_reversible():
    h1 = hash_rd("АА99010112")
    h2 = hash_rd("АА99010112")
    assert h1 == h2
    assert "АА99010112" not in h1
    assert len(h1) == 64  # sha256 hex digest


def test_hash_rd_differs_per_input():
    assert hash_rd("АА99010112") != hash_rd("АА99010113")


def test_issue_and_decode_access_token_roundtrip():
    token = issue_access_token(subject_id="user-1", rd_hash="deadbeef", poe_level="L2")
    claims = decode_access_token(token)
    assert claims["sub"] == "user-1"
    assert claims["rd_hash"] == "deadbeef"
    assert claims["poe_level"] == "L2"
