"""Хороо -> тойрог (district -> constituency) mapping (P3-01).

Versioned like the schema registry (app/schema_registry/service.py): each
import creates a new version rather than mutating rows in place, so a
mid-cycle boundary redraw doesn't retroactively change which reviews counted
as in-jurisdiction for past scoring.

Acceptance: 100% of khoroos map to a constituency — `validate_full_coverage`
is what an import job calls before accepting a new version, not an
afterthought check.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MappingRow:
    khoroo_slug: str
    tovrog_slug: str


def build_mapping_lookup(rows: list[MappingRow]) -> dict[str, str]:
    return {row.khoroo_slug: row.tovrog_slug for row in rows}


def validate_full_coverage(mapping: dict[str, str], all_khoroo_slugs: set[str]) -> list[str]:
    """Returns the khoroos left unmapped — empty list means the import passes
    the "100%" acceptance and can be published as the active version."""
    return sorted(all_khoroo_slugs - mapping.keys())


def jurisdiction_match(
    *, reviewer_khoroo_slug: str | None, entity_tovrog_slug: str | None, mapping: dict[str, str]
) -> bool:
    if reviewer_khoroo_slug is None or entity_tovrog_slug is None:
        return False
    return mapping.get(reviewer_khoroo_slug) == entity_tovrog_slug
