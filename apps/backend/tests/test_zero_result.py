from app.search.zero_result import SearchParams, relax_query, suggest_correction

VOCAB = ["Хаан буудал", "Интермед эмнэлэг", "Улаанбаатар ресторан"]


def test_suggest_correction_finds_close_typo():
    suggestion = suggest_correction("Хан буудал", VOCAB)
    assert suggestion == "Хаан буудал"


def test_suggest_correction_returns_none_for_unrelated_query():
    assert suggest_correction("xyz totally unrelated 12345", VOCAB) is None


def test_relax_query_drops_facets_first():
    params = SearchParams(q="хоол", branch_slug="hool-zoog", category_slug="restoran", facets={"cuisine": "korean"})
    relaxed = relax_query(params)
    assert relaxed.facets == {}
    assert relaxed.category_slug == "restoran"  # not yet dropped


def test_relax_query_then_drops_category():
    params = SearchParams(q="хоол", branch_slug="hool-zoog", category_slug="restoran", facets={})
    relaxed = relax_query(params)
    assert relaxed.category_slug is None
    assert relaxed.branch_slug == "hool-zoog"


def test_relax_query_then_drops_branch():
    params = SearchParams(q="хоол", branch_slug="hool-zoog", category_slug=None, facets={})
    relaxed = relax_query(params)
    assert relaxed.branch_slug is None


def test_relax_query_returns_none_when_nothing_left():
    params = SearchParams(q="хоол")
    assert relax_query(params) is None
