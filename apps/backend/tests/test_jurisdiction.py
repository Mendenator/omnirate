from app.domain.jurisdiction import (
    MappingRow,
    build_mapping_lookup,
    jurisdiction_match,
    validate_full_coverage,
)

ROWS = [
    MappingRow("khan-uul-1", "ub-6"),
    MappingRow("khan-uul-2", "ub-6"),
    MappingRow("bayanzurkh-1", "ub-3"),
]


def test_build_mapping_lookup():
    mapping = build_mapping_lookup(ROWS)
    assert mapping["khan-uul-1"] == "ub-6"
    assert mapping["bayanzurkh-1"] == "ub-3"


def test_validate_full_coverage_empty_when_all_mapped():
    mapping = build_mapping_lookup(ROWS)
    missing = validate_full_coverage(mapping, {"khan-uul-1", "khan-uul-2", "bayanzurkh-1"})
    assert missing == []


def test_validate_full_coverage_reports_unmapped_khoroos():
    mapping = build_mapping_lookup(ROWS)
    missing = validate_full_coverage(mapping, {"khan-uul-1", "songinokhairkhan-1"})
    assert missing == ["songinokhairkhan-1"]


def test_jurisdiction_match_true_for_same_constituency():
    mapping = build_mapping_lookup(ROWS)
    assert jurisdiction_match(reviewer_khoroo_slug="khan-uul-1", entity_tovrog_slug="ub-6", mapping=mapping) is True


def test_jurisdiction_match_false_for_different_constituency():
    mapping = build_mapping_lookup(ROWS)
    assert jurisdiction_match(reviewer_khoroo_slug="khan-uul-1", entity_tovrog_slug="ub-3", mapping=mapping) is False


def test_jurisdiction_match_false_when_reviewer_khoroo_unknown():
    mapping = build_mapping_lookup(ROWS)
    assert jurisdiction_match(reviewer_khoroo_slug=None, entity_tovrog_slug="ub-6", mapping=mapping) is False
