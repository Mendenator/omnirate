"""Medical-context PII redaction (P2-04): diagnosis codes + drug names, layered
on top of the general PII stage (app/domain/moderation.py). Split into its own
module because it only runs on hospital-category reviews — applying it
everywhere would be wasted work and would over-redact unrelated text that
happens to contain a 3-letter-2-digit token.

Acceptance: recall >=97% on a 500-sample set. The drug list below is a
starter set (~20 common OTC/prescription names), not the full Mongolian
pharmacopoeia — see docs/PROGRESS.md for what a production list needs
(a licensed "эмийн толь" data source, which is external to this codebase).
"""

import re

from app.domain.moderation import PiiFinding

# ICD-10 diagnosis codes: a letter, two digits, optional .digit(s) — e.g. "J45.0".
_ICD10_PATTERN = re.compile(r"\b[A-TV-Z][0-9]{2}(?:\.[0-9]{1,2})?\b")

# Starter list — common Mongolian drug names (generic + brand), lowercase for
# case-insensitive matching against lowered text.
_DRUG_NAMES = {
    "парацетамол",
    "ибупрофен",
    "амоксициллин",
    "аспирин",
    "омепразол",
    "метформин",
    "инсулин",
    "лоратадин",
    "цетиризин",
    "дексаметазон",
    "преднизолон",
    "азитромицин",
    "ципрофлоксацин",
    "но-шпа",
    "анальгин",
}
_DRUG_PATTERN = re.compile(r"\b(" + "|".join(re.escape(name) for name in _DRUG_NAMES) + r")\b", re.IGNORECASE)


def find_medical_pii(text: str) -> list[PiiFinding]:
    findings = []
    for match in _ICD10_PATTERN.finditer(text):
        findings.append(PiiFinding(kind="icd10", matched_text=match.group(), start=match.start(), end=match.end()))
    for match in _DRUG_PATTERN.finditer(text):
        findings.append(PiiFinding(kind="drug_name", matched_text=match.group(), start=match.start(), end=match.end()))
    return findings


def redact_medical_pii(text: str) -> tuple[str, list[PiiFinding]]:
    findings = sorted(find_medical_pii(text), key=lambda f: f.start)
    if not findings:
        return text, findings

    out = []
    cursor = 0
    for f in findings:
        if f.start < cursor:
            continue
        out.append(text[cursor : f.start])
        out.append(f"[{f.kind.upper()}_REDACTED]")
        cursor = f.end
    out.append(text[cursor:])
    return "".join(out), findings
