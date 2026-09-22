"""Query understanding (S-14): pulls a location and/or category hint out of a
free-text query so search can filter (not just full-text match) on them —
"Хан-Уул дахь солонгос ресторан" should filter to Хан-Уул + ресторан, with
"солонгос" left as the remaining full-text term.

Dictionary-matching against known slugs/synonyms, not an ML model — the SOW's
own acceptance (300-query test set, >=90% parse accuracy) is exactly what a
lookup-table approach is good at for a closed, known vocabulary (Mongolia's
locations and OmniRate's own categories don't change often enough to need a
trained NER model).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class QueryIntent:
    remaining_text: str
    location_slug: str | None
    category_slug: str | None


def _find_and_strip(query: str, vocabulary: dict[str, str]) -> tuple[str, str | None]:
    """`vocabulary` maps a surface form (e.g. "хан-уул", "солонгос ресторан")
    to its canonical slug. Longest surface form is matched first so a
    multi-word synonym isn't shadowed by a single-word one inside it."""
    lowered = query.lower()
    for surface_form in sorted(vocabulary, key=len, reverse=True):
        if surface_form in lowered:
            idx = lowered.find(surface_form)
            remaining = (query[:idx] + query[idx + len(surface_form) :]).strip()
            remaining = " ".join(remaining.split())  # collapse double spaces left by the removal
            return remaining, vocabulary[surface_form]
    return query, None


def extract_query_intent(
    query: str, *, location_vocabulary: dict[str, str], category_vocabulary: dict[str, str]
) -> QueryIntent:
    after_location, location_slug = _find_and_strip(query, location_vocabulary)
    after_category, category_slug = _find_and_strip(after_location, category_vocabulary)
    return QueryIntent(remaining_text=after_category.strip(), location_slug=location_slug, category_slug=category_slug)
