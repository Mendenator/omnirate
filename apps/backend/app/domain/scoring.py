"""Bayesian trimmed-mean scoring (P1-09), materialized to Redis for O(1) reads.

score = (C * m + Σ w_i * s_i) / (C + Σ w_i)

- s_i: each review's overall_score, after fraud-flagged reviews are dropped
  entirely and the top/bottom `trim_fraction` of the remainder is trimmed
  (bombing/brigading resistance — SOW §5.4: "review bombing ranking-д шууд
  нөлөөлөхгүй").
- w_i: PoE weight (app/domain/poe.poe_weight) — an L4 e-barimt-verified review
  counts far more than an L1 one.
- C, m: Bayesian prior confidence and mean, pulling low-volume entities toward
  the category average instead of letting 1-2 reviews swing the score.

Pure function, no I/O, so it's exactly reproducible against a reference
implementation for the SOW's "4 оронгийн нарийвчлалаар таарах" acceptance.
"""

import math
from dataclasses import dataclass

from app.domain.poe import poe_weight

DEFAULT_FRAUD_THRESHOLD = 0.8
DEFAULT_TRIM_FRACTION = 0.05


@dataclass(frozen=True)
class ScoredReview:
    overall_score: float
    poe_level: str
    fraud_score: float


def compute_bayesian_trimmed_score(
    reviews: list[ScoredReview],
    *,
    prior_mean: float,
    prior_confidence: float,
    trim_fraction: float = DEFAULT_TRIM_FRACTION,
    fraud_threshold: float = DEFAULT_FRAUD_THRESHOLD,
) -> float:
    clean = [r for r in reviews if r.fraud_score < fraud_threshold]
    clean.sort(key=lambda r: r.overall_score)

    n = len(clean)
    trim_n = math.floor(n * trim_fraction)
    trimmed = clean[trim_n : n - trim_n] if n - 2 * trim_n > 0 else clean

    weighted_sum = sum(poe_weight(r.poe_level) * r.overall_score for r in trimmed)
    weight_total = sum(poe_weight(r.poe_level) for r in trimmed)

    numerator = prior_confidence * prior_mean + weighted_sum
    denominator = prior_confidence + weight_total
    return round(numerator / denominator, 4) if denominator > 0 else round(prior_mean, 4)


def compute_criteria_breakdown(criteria_scores_list: list[dict[str, float]]) -> dict[str, float]:
    """Per-criterion average across the reviews that scored it (P1-10 entity
    page's "criteria_breakdown" section). A criterion present on only some
    reviews is averaged over just those, not padded with zeros for the rest."""
    sums: dict[str, float] = {}
    counts: dict[str, int] = {}
    for scores in criteria_scores_list:
        for key, value in scores.items():
            sums[key] = sums.get(key, 0.0) + value
            counts[key] = counts.get(key, 0) + 1
    return {key: round(sums[key] / counts[key], 2) for key in sums}
