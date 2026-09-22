from app.domain.political_scoring import ReviewWithJurisdiction, compute_jurisdiction_separated_scores
from app.domain.scoring import ScoredReview


def _r(score, in_juris):
    return ReviewWithJurisdiction(ScoredReview(overall_score=score, poe_level="L4", fraud_score=0.0), in_juris)


def test_scores_are_computed_independently():
    reviews = [_r(5.0, True), _r(5.0, True), _r(1.0, False), _r(1.0, False)]
    result = compute_jurisdiction_separated_scores(reviews, prior_mean=3.0)

    assert result.in_jurisdiction_score > 3.0  # pulled up by 5.0 reviews
    assert result.out_of_jurisdiction_score < 3.0  # pulled down by 1.0 reviews
    assert result.in_jurisdiction_count == 2
    assert result.out_of_jurisdiction_count == 2


def test_missing_bucket_returns_none_not_prior():
    reviews = [_r(5.0, True)]
    result = compute_jurisdiction_separated_scores(reviews, prior_mean=3.0)
    assert result.out_of_jurisdiction_score is None
    assert result.out_of_jurisdiction_count == 0


def test_empty_reviews_returns_both_none():
    result = compute_jurisdiction_separated_scores([], prior_mean=3.0)
    assert result.in_jurisdiction_score is None
    assert result.out_of_jurisdiction_score is None
