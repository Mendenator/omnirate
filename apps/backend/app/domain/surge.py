"""Surge-mode detection (P2-11): a z-score spike in an entity's review
velocity tightens moderation (routes more reviews to manual queue, lowers
the LLM-sampling confidence bar) rather than blocking outright — a real
product launch or news mention also spikes review velocity, and surge mode
must not punish that.

Acceptance: activates within 5 minutes of z-score >4. The 5-minute budget is
an operational property of how often app/domain/surge_service.py's check
runs (a cron/stream consumer), not something this pure function can assert.
"""

import statistics
from dataclasses import dataclass

SURGE_Z_SCORE_THRESHOLD = 4.0
MIN_HISTORY_BUCKETS_FOR_SIGNAL = 6  # need enough history that stdev is meaningful


@dataclass(frozen=True)
class SurgeCheckResult:
    z_score: float
    is_surge: bool


def compute_z_score(current_count: int, historical_counts: list[int]) -> float:
    if len(historical_counts) < 2:
        return 0.0
    mean = statistics.mean(historical_counts)
    stdev = statistics.pstdev(historical_counts)
    if stdev == 0:
        return 0.0 if current_count == mean else float("inf")
    return (current_count - mean) / stdev


def check_surge(current_count: int, historical_counts: list[int]) -> SurgeCheckResult:
    if len(historical_counts) < MIN_HISTORY_BUCKETS_FOR_SIGNAL:
        return SurgeCheckResult(z_score=0.0, is_surge=False)  # not enough history to judge yet
    z = compute_z_score(current_count, historical_counts)
    return SurgeCheckResult(z_score=z, is_surge=z > SURGE_Z_SCORE_THRESHOLD)
