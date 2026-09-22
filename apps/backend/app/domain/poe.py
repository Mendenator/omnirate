"""Proof-of-Experience level/weight engine (P1-05).

SOW references "PRD-ийн L0–L4 хүснэгтийн 100% тест кейс" — the exact weight
table lives in the (separate) Technical PRD, not in the SOW itself. The table
below is a placeholder consistent with the SOW's stated targets (K3: PoE>=L2
share >=70%, ranking formula weights verified reviews) — swap in the PRD's
real numbers before P1 sign-off; every call site takes the table as data, not
a hardcoded constant, so that swap is a one-line change.

Evidence -> level:
  L0 — no evidence (score still counted, weight 0 in ranking's N_verified term)
  L1 — OTP-verified identity only, no purchase evidence
  L2 — GPS dwell-time evidence (P2-01) suggests presence
  L3 — OCR-parsed receipt evidence, not yet e-barimt-matched
  L4 — e-barimt QR verified against ТТД (P1-01), highest trust
"""

from dataclasses import dataclass
from enum import StrEnum


class PoeLevel(StrEnum):
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"


@dataclass(frozen=True)
class PoeLevelSpec:
    weight: float  # contribution to N_verified in the ranking formula (5.4)
    counts_as_verified: bool  # counted toward K3 (PoE>=L2 share)


POE_LEVEL_TABLE: dict[PoeLevel, PoeLevelSpec] = {
    PoeLevel.L0: PoeLevelSpec(weight=0.0, counts_as_verified=False),
    PoeLevel.L1: PoeLevelSpec(weight=0.15, counts_as_verified=False),
    PoeLevel.L2: PoeLevelSpec(weight=0.55, counts_as_verified=True),
    PoeLevel.L3: PoeLevelSpec(weight=0.8, counts_as_verified=True),
    PoeLevel.L4: PoeLevelSpec(weight=1.0, counts_as_verified=True),
}


def evidence_kinds_to_level(evidence_kinds: set[str]) -> PoeLevel:
    """Highest level supportable by the evidence attached to a review.

    Ordering matches app/domain/models.PoeEvidence.kind: e_barimt > ocr_receipt > gps.
    """
    if "e_barimt" in evidence_kinds:
        return PoeLevel.L4
    if "ocr_receipt" in evidence_kinds:
        return PoeLevel.L3
    if "gps" in evidence_kinds:
        return PoeLevel.L2
    return PoeLevel.L1


def poe_weight(level: str) -> float:
    return POE_LEVEL_TABLE[PoeLevel(level)].weight


def counts_as_verified(level: str) -> bool:
    return POE_LEVEL_TABLE[PoeLevel(level)].counts_as_verified
