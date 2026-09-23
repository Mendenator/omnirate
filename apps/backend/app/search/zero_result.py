"""Zero-result fallback (S-15): "Та ... гэж хайсан уу?" spelling suggestion +
progressively relaxed query. K11 acceptance: zero-result rate <=3% — this
module is the mitigation, the rate itself is measured from search logs
(infra/observability's Grafana panel), not computed here.

`difflib.get_close_matches` (stdlib) rather than a fuzzy-matching library —
this is a small, closed vocabulary (entity names + synonyms), and stdlib
Levenshtein-ish matching is both sufficient and dependency-free.
"""

import difflib
from dataclasses import dataclass, field


def suggest_correction(query: str, vocabulary: list[str], *, cutoff: float = 0.6) -> str | None:
    matches = difflib.get_close_matches(query, vocabulary, n=1, cutoff=cutoff)
    return matches[0] if matches else None


@dataclass(frozen=True)
class SearchParams:
    q: str | None = None
    branch_slug: str | None = None
    category_slug: str | None = None
    facets: dict[str, str] = field(default_factory=dict)


def relax_query(params: SearchParams) -> SearchParams | None:
    """Drops the most restrictive filter first (facets, then category, then
    branch), returning None once nothing is left to relax — the caller
    should stop retrying at that point rather than loop forever.
    """
    if params.facets:
        return SearchParams(q=params.q, branch_slug=params.branch_slug, category_slug=params.category_slug, facets={})
    if params.category_slug:
        return SearchParams(q=params.q, branch_slug=params.branch_slug, category_slug=None, facets={})
    if params.branch_slug:
        return SearchParams(q=params.q, branch_slug=None, category_slug=None, facets={})
    return None
