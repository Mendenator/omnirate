"""S-17 acceptance: a simulated review-bombing attack must not move an
entity's rank position by more than 2 tiers. This composes two pieces built
earlier rather than adding new production code: fraud-score exclusion in
app/domain/scoring.py (P1-09) and the ranking formula in app/search/ranking.py
(S-07) — this test is what makes the S-17 acceptance criterion *checked*,
not just assumed to follow from the other two.
"""

from app.domain.scoring import ScoredReview, compute_bayesian_trimmed_score
from app.search.ranking import RankingInput, rank_score

PRIOR_MEAN = 3.5
PRIOR_CONFIDENCE = 10.0


def _entity_rank(bayes_score: float, n_verified: int) -> float:
    return rank_score(
        RankingInput(
            bm25_score=5.0,
            bm25_max_in_result_set=5.0,
            bayes_score=bayes_score,
            n_verified=n_verified,
            n_verified_max_in_result_set=20,
            distance_km=1.0,
            age_days=30,
        )
    )


def _positions(scores: dict[str, float]) -> dict[str, int]:
    ordered = sorted(scores, key=lambda k: scores[k], reverse=True)
    return {entity_id: i for i, entity_id in enumerate(ordered)}


def test_bombing_attack_moves_target_at_most_two_ranks():
    # Five candidate entities with distinct, well-separated baseline quality.
    baseline_reviews = {
        "e1": [ScoredReview(overall_score=4.8, poe_level="L4", fraud_score=0.0) for _ in range(15)],
        "e2": [ScoredReview(overall_score=4.5, poe_level="L4", fraud_score=0.0) for _ in range(12)],
        "e3": [ScoredReview(overall_score=4.0, poe_level="L3", fraud_score=0.0) for _ in range(10)],
        "e4": [ScoredReview(overall_score=3.5, poe_level="L2", fraud_score=0.0) for _ in range(8)],
        "e5": [ScoredReview(overall_score=3.0, poe_level="L2", fraud_score=0.0) for _ in range(6)],
    }

    baseline_scores = {
        eid: _entity_rank(
            compute_bayesian_trimmed_score(reviews, prior_mean=PRIOR_MEAN, prior_confidence=PRIOR_CONFIDENCE),
            len(reviews),
        )
        for eid, reviews in baseline_reviews.items()
    }
    baseline_positions = _positions(baseline_scores)
    target = "e1"
    assert baseline_positions[target] == 0  # e1 starts in first place

    # Attack: 200 fraud-flagged 1-star reviews dumped on the leader. A real
    # fraud pipeline (P2-08's LightGBM model, P2-09's graph clustering) is
    # what would assign these a high fraud_score in production; this test
    # asserts the *consequence* of that flagging on rank, not the detector.
    bombed_reviews = {
        **baseline_reviews,
        "e1": baseline_reviews["e1"]
        + [ScoredReview(overall_score=1.0, poe_level="L1", fraud_score=0.95) for _ in range(200)],
    }
    bombed_scores = {
        eid: _entity_rank(
            compute_bayesian_trimmed_score(reviews, prior_mean=PRIOR_MEAN, prior_confidence=PRIOR_CONFIDENCE),
            len(reviews),
        )
        for eid, reviews in bombed_reviews.items()
    }
    bombed_positions = _positions(bombed_scores)

    assert abs(bombed_positions[target] - baseline_positions[target]) <= 2


def test_unflagged_low_quality_reviews_do_still_affect_rank():
    # Sanity check the test above isn't vacuous: reviews that AREN'T fraud-
    # flagged (fraud_score=0) genuinely do drag score down — the system
    # isn't simply ignoring negative reviews, only ones caught as fraud.
    clean = [ScoredReview(overall_score=4.8, poe_level="L4", fraud_score=0.0) for _ in range(15)]
    clean_score = compute_bayesian_trimmed_score(clean, prior_mean=PRIOR_MEAN, prior_confidence=PRIOR_CONFIDENCE)

    with_genuine_negatives = clean + [
        ScoredReview(overall_score=1.0, poe_level="L4", fraud_score=0.0) for _ in range(15)
    ]
    negative_score = compute_bayesian_trimmed_score(
        with_genuine_negatives, prior_mean=PRIOR_MEAN, prior_confidence=PRIOR_CONFIDENCE
    )

    assert negative_score < clean_score
