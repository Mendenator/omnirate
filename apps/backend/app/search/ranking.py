"""Ranking v1 (S-07), implementing SOW §5.4's formula exactly:

    score = 0.45*BM25_norm + 0.20*Bayes_norm + 0.15*log(1+N_verified)/log(1+N_max)
          + 0.12*exp(-d/2km) + 0.08*freshness

Weights are tuned against the gold set (S-08) via NDCG@10, not hardcoded
folklore — they're module-level constants specifically so a tuning pass can
change them without touching call sites.
"""

import math
from dataclasses import dataclass

W_BM25 = 0.45
W_BAYES = 0.20
W_VERIFIED = 0.15
W_DISTANCE = 0.12
W_FRESHNESS = 0.08

DISTANCE_DECAY_KM = 2.0
FRESHNESS_HALF_LIFE_DAYS = 180.0


@dataclass(frozen=True)
class RankingInput:
    bm25_score: float
    bm25_max_in_result_set: float
    bayes_score: float  # already 0..5 from app.domain.scoring
    n_verified: int
    n_verified_max_in_result_set: int
    distance_km: float | None
    age_days: float


def _safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator > 0 else 0.0


def rank_score(inp: RankingInput) -> float:
    bm25_norm = _safe_div(inp.bm25_score, inp.bm25_max_in_result_set)
    bayes_norm = inp.bayes_score / 5.0

    verified_term = _safe_div(
        math.log1p(inp.n_verified), math.log1p(max(inp.n_verified_max_in_result_set, inp.n_verified))
    )

    distance_term = math.exp(-inp.distance_km / DISTANCE_DECAY_KM) if inp.distance_km is not None else 0.0

    # Freshness decays exponentially with a ~180-day half life rather than a
    # hard cliff, so a 6-month-old entity isn't scored identically to a
    # brand-new one just because both are "old enough."
    freshness_term = math.exp(-math.log(2) * inp.age_days / FRESHNESS_HALF_LIFE_DAYS)

    return (
        W_BM25 * bm25_norm
        + W_BAYES * bayes_norm
        + W_VERIFIED * verified_term
        + W_DISTANCE * distance_term
        + W_FRESHNESS * freshness_term
    )
