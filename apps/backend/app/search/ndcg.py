"""NDCG@k evaluation (S-08), used both as a library function and by
infra/search-eval/run_ndcg_eval.py's CI regression gate (DoD: a change that
drops gold-set NDCG@10 by more than 0.02 blocks merge).
"""

import math


def dcg_at_k(relevance_grades: list[int], k: int) -> float:
    """relevance_grades[i] is the human-labeled relevance (0-3 typically) of
    the result at rank i (0-indexed)."""
    return sum(grade / math.log2(rank + 2) for rank, grade in enumerate(relevance_grades[:k]))


def ndcg_at_k(relevance_grades: list[int], k: int = 10) -> float:
    actual_dcg = dcg_at_k(relevance_grades, k)
    ideal_dcg = dcg_at_k(sorted(relevance_grades, reverse=True), k)
    return actual_dcg / ideal_dcg if ideal_dcg > 0 else 0.0


def ndcg_for_query(ranked_entity_ids: list[str], relevance_by_entity_id: dict[str, int], k: int = 10) -> float:
    """Looks up each returned result's gold-set relevance grade (0 if the
    result isn't in the gold set at all — an unjudged/irrelevant result)."""
    grades = [relevance_by_entity_id.get(eid, 0) for eid in ranked_entity_ids]
    return ndcg_at_k(grades, k)
