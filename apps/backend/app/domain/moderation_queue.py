"""Two-moderator consensus workflow (P2-12): a case needs verdicts from 2
distinct moderators. If they agree, the case resolves with that verdict. If
they disagree, it escalates rather than picking a side automatically — a
disagreement between two trained moderators is itself the signal that the
case needs a senior/third opinion, not a coin flip.

Target: median resolution time <=3min — an operational property tracked via
`ModerationCase.created_at`/`resolved_at` timestamps (app/domain/models.py),
not something this pure function can assert on its own.
"""

from collections import Counter
from dataclasses import dataclass
from enum import StrEnum


class Verdict(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"


class CaseState(StrEnum):
    AWAITING_FIRST_DECISION = "awaiting_first_decision"
    AWAITING_SECOND_DECISION = "awaiting_second_decision"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


@dataclass(frozen=True)
class Decision:
    moderator_id: str
    verdict: Verdict


@dataclass(frozen=True)
class CaseOutcome:
    state: CaseState
    final_verdict: Verdict | None


def resolve_case(decisions: list[Decision]) -> CaseOutcome:
    distinct_moderators = {d.moderator_id for d in decisions}
    if len(distinct_moderators) != len(decisions):
        raise ValueError("the same moderator cannot cast two decisions on one case")

    if len(decisions) == 0:
        return CaseOutcome(state=CaseState.AWAITING_FIRST_DECISION, final_verdict=None)
    if len(decisions) == 1:
        return CaseOutcome(state=CaseState.AWAITING_SECOND_DECISION, final_verdict=None)

    verdict_counts = Counter(d.verdict for d in decisions[:2])
    if len(verdict_counts) == 1:
        return CaseOutcome(state=CaseState.RESOLVED, final_verdict=decisions[0].verdict)
    return CaseOutcome(state=CaseState.ESCALATED, final_verdict=None)
