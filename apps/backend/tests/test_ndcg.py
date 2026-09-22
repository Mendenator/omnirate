from app.search.ndcg import ndcg_at_k, ndcg_for_query


def test_perfect_ranking_scores_1():
    assert ndcg_at_k([3, 2, 1, 0], k=4) == 1.0


def test_reversed_ranking_scores_below_1():
    assert ndcg_at_k([0, 1, 2, 3], k=4) < 1.0


def test_empty_relevance_is_zero():
    assert ndcg_at_k([], k=10) == 0.0


def test_all_zero_relevance_is_zero():
    assert ndcg_at_k([0, 0, 0], k=10) == 0.0


def test_ndcg_for_query_treats_unjudged_results_as_irrelevant():
    ranked = ["e1", "e2", "e3"]
    relevance = {"e1": 3, "e3": 1}  # e2 is unjudged -> grade 0
    score = ndcg_for_query(ranked, relevance, k=3)
    ideal = ndcg_at_k([3, 1, 0], k=3)
    actual = ndcg_at_k([3, 0, 1], k=3)
    assert score == actual
    assert actual <= ideal
