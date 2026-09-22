from app.domain.moderation import find_pii, redact_pii


def test_detects_rd():
    findings = find_pii("Миний РД АБ12345678 байна")
    assert any(f.kind == "rd" for f in findings)


def test_detects_phone():
    findings = find_pii("Утас: 99112233")
    assert any(f.kind == "phone" for f in findings)


def test_detects_email():
    findings = find_pii("Холбогдох: user@example.com")
    assert any(f.kind == "email" for f in findings)


def test_clean_text_has_no_findings():
    findings = find_pii("Энэ ресторан их сайн байсан, хоол амттай.")
    assert findings == []


def test_redact_replaces_matched_spans():
    text = "Намайг user@example.com дээр ол"
    redacted, findings = redact_pii(text)
    assert "user@example.com" not in redacted
    assert "[EMAIL_REDACTED]" in redacted
    assert len(findings) == 1


def test_redact_handles_multiple_findings_without_index_drift():
    text = "email: a@b.com утас: 91234567"
    redacted, findings = redact_pii(text)
    assert "a@b.com" not in redacted
    assert "91234567" not in redacted
    assert len(findings) == 2
