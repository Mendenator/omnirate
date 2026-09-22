import base64
import hashlib

from app.core.dan_auth import build_authorize_url, generate_pkce_pair


def test_pkce_challenge_matches_s256_of_verifier():
    pair = generate_pkce_pair()
    expected = base64.urlsafe_b64encode(hashlib.sha256(pair.verifier.encode()).digest()).rstrip(b"=").decode()
    assert pair.challenge == expected


def test_pkce_pairs_are_unique():
    a, b = generate_pkce_pair(), generate_pkce_pair()
    assert a.verifier != b.verifier
    assert a.challenge != b.challenge


def test_authorize_url_includes_pkce_and_state():
    pair = generate_pkce_pair()
    url = build_authorize_url(redirect_uri="https://app.omnirate.mn/callback", state="xyz", pkce=pair)
    assert "code_challenge=" + pair.challenge in url
    assert "code_challenge_method=S256" in url
    assert "state=xyz" in url
