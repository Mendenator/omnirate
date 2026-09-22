"""Moderation stage 1: PII regex detection (P1-07).

Acceptance: PII recall >=99% on the test set. Regex is deliberately permissive
(favors recall over precision — a false-positive redaction is cheap, a missed
national ID leaking in a public review is not) since this is stage 1 of a
multi-stage pipeline (stage 2: XLM-R toxicity classifier, P1-08).
"""

import re
from dataclasses import dataclass

# РД: 2 Cyrillic letters + 8 digits (е.g. АБ12345678). Case-insensitive,
# optional space/hyphen between letters and digits.
_RD_PATTERN = re.compile(r"\b[А-ЯЁӨҮа-яёөү]{2}[\s-]?\d{8}\b")

# Mongolian mobile: 8 digits, optionally prefixed +976 / 976 / 00976.
_PHONE_PATTERN = re.compile(r"(?:\+?976|00976)?[\s-]?\b\d{8}\b")

_EMAIL_PATTERN = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")

PII_PATTERNS: dict[str, re.Pattern] = {
    "rd": _RD_PATTERN,
    "phone": _PHONE_PATTERN,
    "email": _EMAIL_PATTERN,
}


@dataclass(frozen=True)
class PiiFinding:
    kind: str
    matched_text: str
    start: int
    end: int


def find_pii(text: str) -> list[PiiFinding]:
    findings: list[PiiFinding] = []
    for kind, pattern in PII_PATTERNS.items():
        for match in pattern.finditer(text):
            findings.append(PiiFinding(kind=kind, matched_text=match.group(), start=match.start(), end=match.end()))
    return findings


def redact_pii(text: str) -> tuple[str, list[PiiFinding]]:
    findings = find_pii(text)
    if not findings:
        return text, findings

    # Redact longest-match-first so overlapping spans (e.g. phone pattern
    # matching inside an RD match) don't leave partial digits exposed.
    findings_sorted = sorted(findings, key=lambda f: f.start)
    redacted = []
    cursor = 0
    for f in findings_sorted:
        if f.start < cursor:
            continue  # overlapped with a previous redaction, already covered
        redacted.append(text[cursor : f.start])
        redacted.append(f"[{f.kind.upper()}_REDACTED]")
        cursor = f.end
    redacted.append(text[cursor:])
    return "".join(redacted), findings
