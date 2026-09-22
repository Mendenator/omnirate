from app.search.query_understanding import extract_query_intent

LOCATIONS = {"хан-уул": "khan-uul", "баянзүрх": "bayanzurkh"}
CATEGORIES = {"ресторан": "restoran", "эмнэлэг": "emneleg"}


def test_extracts_location_and_category_leaving_remainder():
    intent = extract_query_intent("Хан-Уул дахь солонгос ресторан", location_vocabulary=LOCATIONS, category_vocabulary=CATEGORIES)
    assert intent.location_slug == "khan-uul"
    assert intent.category_slug == "restoran"
    assert "солонгос" in intent.remaining_text
    assert "хан-уул" not in intent.remaining_text.lower()


def test_query_with_only_category():
    intent = extract_query_intent("хямд эмнэлэг хайж байна", location_vocabulary=LOCATIONS, category_vocabulary=CATEGORIES)
    assert intent.category_slug == "emneleg"
    assert intent.location_slug is None


def test_query_with_neither_leaves_everything_as_remainder():
    intent = extract_query_intent("hool sh", location_vocabulary=LOCATIONS, category_vocabulary=CATEGORIES)
    assert intent.location_slug is None
    assert intent.category_slug is None
    assert intent.remaining_text == "hool sh"
