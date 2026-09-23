from app.domain.defamation import (
    check_strict_defamation,
    contains_criminal_allegation,
    has_cited_source,
)


def test_unsourced_criminal_allegation_is_blocked():
    result = check_strict_defamation("Энэ хүн хээл хахууль авсан гэдгийг мэднэ")
    assert result.is_blocked is True
    assert result.reason == "unsourced_criminal_allegation"


def test_sourced_criminal_allegation_is_not_blocked():
    result = check_strict_defamation(
        "Шүүхийн шийдвэрээр хээл хахууль авсан нь тогтоогдсон (эх сурвалж: https://example.mn/news/123)"
    )
    assert result.is_blocked is False


def test_ordinary_criticism_without_allegation_is_not_blocked():
    result = check_strict_defamation("Энэ гишүүн хуралдаанд ховор ирдэг гэж боддог")
    assert result.is_blocked is False


def test_contains_criminal_allegation_detects_keyword():
    assert contains_criminal_allegation("тэр хулгайлсан") is True
    assert contains_criminal_allegation("сайн ажилладаг хүн") is False


def test_has_cited_source_detects_url():
    assert has_cited_source("дэлгэрэнгүй: https://news.mn/123") is True
    assert has_cited_source("энгийн сэтгэгдэл") is False


def test_has_cited_source_detects_court_decision_reference():
    assert has_cited_source("2025 оны 4-р сарын тогтоол") is True
