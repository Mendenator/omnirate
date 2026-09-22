import pytest

from app.ml.ocr import _parse_fields_from_text, run_paddleocr


def test_parse_fields_extracts_amount_and_date():
    text = "Хаан буудал\nХоол зоог\nНИЙТ ДҮН: 45,000.00\n2026-09-15"
    fields = _parse_fields_from_text(text)
    assert fields.merchant_name == "Хаан буудал"
    assert fields.amount == 45000.0
    assert fields.purchased_at_raw == "2026-09-15"


def test_parse_fields_handles_missing_amount():
    fields = _parse_fields_from_text("random receipt text with no total line")
    assert fields.amount is None


def test_run_paddleocr_raises_clear_not_implemented_error():
    with pytest.raises(NotImplementedError, match="PaddleOCR"):
        run_paddleocr(b"fake-bytes")
