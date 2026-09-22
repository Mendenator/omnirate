from app.domain.medical_pii import find_medical_pii, redact_medical_pii


def test_detects_icd10_code():
    findings = find_medical_pii("Онош: J45.0 бронхийн багтраа")
    assert any(f.kind == "icd10" and f.matched_text == "J45.0" for f in findings)


def test_detects_drug_name_case_insensitively():
    findings = find_medical_pii("Парацетамол өгсөн")
    assert any(f.kind == "drug_name" for f in findings)


def test_clean_medical_text_has_no_findings():
    findings = find_medical_pii("Эмч маш анхааралтай, найрсаг байлаа")
    assert findings == []


def test_redact_replaces_icd10_and_drug():
    text = "Онош J45.0, эм: ибупрофен"
    redacted, findings = redact_medical_pii(text)
    assert "J45.0" not in redacted
    assert "ибупрофен" not in redacted
    assert len(findings) == 2
