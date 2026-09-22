"""Receipt OCR (P1-03). ⛔ The PaddleOCR model itself, and the field-accuracy
tuning that gets this to the ">=90% field accuracy, p95<=8s" acceptance, both
need a labeled receipt dataset (same external blocker as P0-12 — see
docs/PROGRESS.md). This module is the pipeline shape that consumes the
model's output; swapping the placeholder regex parse for a fine-tuned
field-extraction model is a change inside `_parse_fields_from_text` only —
callers (app/api/v1) don't need to change.
"""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ReceiptFields:
    merchant_name: str | None
    amount: float | None
    purchased_at_raw: str | None
    raw_text: str


_AMOUNT_PATTERN = re.compile(r"(?:НИЙТ|ДҮН|TOTAL)\D{0,10}([\d,]+\.?\d*)", re.IGNORECASE)
_DATE_PATTERN = re.compile(r"\b(\d{4}[-./]\d{2}[-./]\d{2})\b")


def run_paddleocr(image_bytes: bytes) -> str:
    """Real implementation calls `paddleocr.PaddleOCR(lang="cyrillic")` on the
    decoded image and joins detected text lines. Left as an explicit stub
    (not a silent no-op) so a caller that forgets to install the model gets
    a clear error rather than empty OCR results being mistaken for "no text
    found on receipt."
    """
    raise NotImplementedError(
        "PaddleOCR model not installed in this environment — see docs/PROGRESS.md P1-03. "
        "Once available: PaddleOCR(lang='cyrillic').ocr(image_bytes) and join text lines here."
    )


def _parse_fields_from_text(raw_text: str) -> ReceiptFields:
    amount_match = _AMOUNT_PATTERN.search(raw_text)
    date_match = _DATE_PATTERN.search(raw_text)
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    return ReceiptFields(
        merchant_name=lines[0] if lines else None,
        amount=float(amount_match.group(1).replace(",", "")) if amount_match else None,
        purchased_at_raw=date_match.group(1) if date_match else None,
        raw_text=raw_text,
    )


def extract_receipt_fields(image_bytes: bytes) -> ReceiptFields:
    raw_text = run_paddleocr(image_bytes)
    return _parse_fields_from_text(raw_text)
