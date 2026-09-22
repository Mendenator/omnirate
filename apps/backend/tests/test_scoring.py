from app.domain.scoring import ScoredReview, compute_bayesian_trimmed_score


def test_no_reviews_returns_prior_mean():
    score = compute_bayesian_trimmed_score([], prior_mean=4.0, prior_confidence=10)
    assert score == 4.0


def test_single_high_confidence_review_pulled_toward_prior():
    reviews = [ScoredReview(overall_score=5.0, poe_level="L4", fraud_score=0.0)]
    score = compute_bayesian_trimmed_score(reviews, prior_mean=3.0, prior_confidence=10)
    # (10*3 + 1.0*5) / (10 + 1.0) = 35/11 = 3.1818
    assert score == 3.1818


def test_fraud_flagged_reviews_are_excluded():
    reviews = [
        ScoredReview(overall_score=5.0, poe_level="L4", fraud_score=0.0),
        ScoredReview(overall_score=1.0, poe_level="L4", fraud_score=0.95),  # fraud -> dropped
    ]
    with_fraud = compute_bayesian_trimmed_score(reviews, prior_mean=3.0, prior_confidence=10)
    without_fraud_review = compute_bayesian_trimmed_score(reviews[:1], prior_mean=3.0, prior_confidence=10)
    assert with_fraud == without_fraud_review


def test_l0_unverified_review_has_zero_weight():
    reviews = [ScoredReview(overall_score=1.0, poe_level="L0", fraud_score=0.0)]
    score = compute_bayesian_trimmed_score(reviews, prior_mean=3.0, prior_confidence=10)
    assert score == 3.0  # L0 weight is 0 -> falls back entirely to the prior


def test_trimming_removes_extreme_outliers():
    # 20 reviews at 4.0, plus one bombing outlier at 0.0 -> trim_fraction=0.05
    # drops ~1 review from each tail, so the 0.0 outlier is excluded.
    reviews = [ScoredReview(overall_score=4.0, poe_level="L4", fraud_score=0.0) for _ in range(20)]
    reviews.append(ScoredReview(overall_score=0.0, poe_level="L4", fraud_score=0.0))
    score = compute_bayesian_trimmed_score(reviews, prior_mean=4.0, prior_confidence=10, trim_fraction=0.05)
    assert score == 4.0
