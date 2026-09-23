"""strict_defamation moderation mode (P3-04): applies only to political-branch
reviews. An unsourced criminal accusation is rejected outright — before the
LLM/heuristic pipeline even runs — because the cost of a false negative here
(a defamatory allegation going live) is categorically worse than the cost of
a false positive (a legitimate, sourced criticism getting extra scrutiny).

Acceptance: 0 unsourced criminal_allegation publications on a 500-case test
set. The keyword list is deliberately broad/recall-favoring for the same
reason app/domain/moderation.py's PII patterns are — see that module's
docstring for the same recall-over-precision reasoning.
"""

import re
from dataclasses import dataclass

_CRIMINAL_ALLEGATION_PATTERNS = [
    r"\bхулгай(лсан|дсан)?\b",
    r"\bхээл\s*хахууль\b",
    r"\bавлига(тай|ач)?\b",
    r"\bмэхэлсэн\b",
    r"\bгэмт хэрэг(тэн)?\b",
    r"\bшоронд\s*(орсон|суусан)\b",
    r"\bалуурчин\b",
    r"\bхуурамч\s*баримт\b",
]
_CRIMINAL_ALLEGATION_RE = re.compile("|".join(_CRIMINAL_ALLEGATION_PATTERNS), re.IGNORECASE)

_SOURCE_CITATION_PATTERNS = [
    r"https?://\S+",
    r"эх\s*сурвалж\s*[:\-]",
    r"шүүхийн\s*шийдвэр",
    r"\b\d{4}\s*оны\s+\S+(?:\s+\S+){0,3}\s+тогтоол",  # e.g. "2025 оны 4-р сарын тогтоол"
]
_SOURCE_CITATION_RE = re.compile("|".join(_SOURCE_CITATION_PATTERNS), re.IGNORECASE)


@dataclass(frozen=True)
class DefamationCheckResult:
    is_blocked: bool
    reason: str | None


def contains_criminal_allegation(text: str) -> bool:
    return bool(_CRIMINAL_ALLEGATION_RE.search(text))


def has_cited_source(text: str) -> bool:
    return bool(_SOURCE_CITATION_RE.search(text))


def check_strict_defamation(text: str) -> DefamationCheckResult:
    if contains_criminal_allegation(text) and not has_cited_source(text):
        return DefamationCheckResult(is_blocked=True, reason="unsourced_criminal_allegation")
    return DefamationCheckResult(is_blocked=False, reason=None)
