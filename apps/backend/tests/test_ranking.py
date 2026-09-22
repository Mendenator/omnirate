import math

from app.search.ranking import RankingInput, rank_score


def _base_input(**overrides) -> RankingInput:
    defaults = dict(
        bm25_score=5.0,
        bm25_max_in_result_set=10.0,
        bayes_score=4.0,
        n_verified=5,
        n_verified_max_in_result_set=10,
        distance_km=1.0,
        age_days=0.0,
    )
    defaults.update(overrides)
    return RankingInput(**defaults)


def test_score_is_between_0_and_1_for_typical_input():
    score = rank_score(_base_input())
    assert 0.0 <= score <= 1.0


def test_higher_bm25_increases_score_all_else_equal():
    low = rank_score(_base_input(bm25_score=1.0))
    high = rank_score(_base_input(bm25_score=9.0))
    assert high > low


def test_farther_distance_decreases_score():
    near = rank_score(_base_input(distance_km=0.1))
    far = rank_score(_base_input(distance_km=20.0))
    assert near > far


def test_older_entity_scores_lower_than_freshly_added():
    fresh = rank_score(_base_input(age_days=0))
    old = rank_score(_base_input(age_days=365 * 2))
    assert fresh > old


def test_zero_bm25_max_does_not_divide_by_zero():
    score = rank_score(_base_input(bm25_score=0.0, bm25_max_in_result_set=0.0))
    assert math.isfinite(score)


def test_no_distance_contributes_zero_distance_term():
    score = rank_score(_base_input(distance_km=None))
    assert math.isfinite(score)
