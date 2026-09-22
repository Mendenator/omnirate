"""Notice-and-takedown SLA logic (P3-05/P3-06).

Two request classes share one table (app/domain/models.TakedownRequest),
distinguished by `requester_type`: a regular user's takedown request gets the
default SLA (72h); a law-enforcement request gets the tighter 4h SLA the
portal (P3-06) promises. Keeping them in one table/one audit trail — rather
than two parallel systems — is what makes the hash-chain in
app/domain/audit.py cover both without a merge step.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum


class RequesterType(StrEnum):
    USER = "user"
    LAW_ENFORCEMENT = "law_enforcement"


class TakedownStatus(StrEnum):
    OPEN = "open"
    REVIEWING = "reviewing"
    RESOLVED = "resolved"
    REJECTED = "rejected"


SLA_HOURS = {
    RequesterType.USER: 72,
    RequesterType.LAW_ENFORCEMENT: 4,
}


def compute_sla_deadline(*, requester_type: RequesterType, created_at: datetime) -> datetime:
    return created_at + timedelta(hours=SLA_HOURS[requester_type])


@dataclass(frozen=True)
class SlaCheckResult:
    is_breached: bool
    hours_remaining: float


def check_sla(*, deadline: datetime, now: datetime, status: TakedownStatus) -> SlaCheckResult:
    if status in (TakedownStatus.RESOLVED, TakedownStatus.REJECTED):
        return SlaCheckResult(is_breached=False, hours_remaining=0.0)
    remaining = (deadline - now).total_seconds() / 3600
    return SlaCheckResult(is_breached=remaining < 0, hours_remaining=remaining)
