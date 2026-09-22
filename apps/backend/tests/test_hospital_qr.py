import time
from unittest.mock import patch

import pytest

from app.core.hospital_qr import HospitalQrPayload, QrVerificationError, generate_hospital_qr, verify_hospital_qr


def test_generate_then_verify_roundtrip():
    token = generate_hospital_qr("entity-123")
    payload = verify_hospital_qr(token)
    assert payload.entity_id == "entity-123"


def test_tampered_payload_fails_signature_check():
    token = generate_hospital_qr("entity-123")
    payload_b64, sig_b64 = token.split(".", 1)
    tampered = payload_b64 + "x." + sig_b64  # corrupt the payload
    with pytest.raises(QrVerificationError) as exc_info:
        verify_hospital_qr(tampered)
    assert exc_info.value.reason_code in ("malformed_token", "invalid_signature")


def test_expired_token_is_rejected():
    token = generate_hospital_qr("entity-123")
    with patch("app.core.hospital_qr.time.time", return_value=time.time() + 73 * 3600):
        with pytest.raises(QrVerificationError) as exc_info:
            verify_hospital_qr(token)
    assert exc_info.value.reason_code == "expired"


def test_malformed_token_rejected():
    with pytest.raises(QrVerificationError) as exc_info:
        verify_hospital_qr("not-a-valid-token")
    assert exc_info.value.reason_code == "malformed_token"


def test_each_token_has_a_unique_jti():
    a = verify_hospital_qr(generate_hospital_qr("entity-123"))
    b = verify_hospital_qr(generate_hospital_qr("entity-123"))
    assert a.jti != b.jti
