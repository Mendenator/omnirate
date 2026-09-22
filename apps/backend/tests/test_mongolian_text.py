from app.search.mongolian_text import (
    build_query_variants,
    fold_vowels,
    is_latin_query,
    light_stem,
    transliterate_latin_to_cyrillic,
)


def test_fold_vowels_flattens_o_and_u_umlaut():
    assert fold_vowels("өргөө") == "оргоо"
    assert fold_vowels("үнэгүй") == "унэгуй"


def test_fold_vowels_leaves_ascii_untouched():
    assert fold_vowels("restoran123") == "restoran123"


def test_is_latin_query_detects_ascii():
    assert is_latin_query("hool") is True
    assert is_latin_query("хоол") is False


def test_transliterate_hool_to_khool_family():
    # "hool" -> "h"->х, "oo"->оо, "l"->л => "хоол"
    assert transliterate_latin_to_cyrillic("hool") == "хоол"


def test_transliterate_urgoo():
    # "urgoo" -> u->ү, r->р, g->г, oo->оо, l? no l here => "ургоо"
    assert transliterate_latin_to_cyrillic("urgoo") == "ургоо"


def test_light_stem_strips_known_suffix():
    assert light_stem("хоолтой") == "хоол"
    assert light_stem("рестораас") == "рестор"


def test_light_stem_leaves_unmatched_words_unchanged():
    assert light_stem("сайн") == "сайн"


def test_light_stem_does_not_amputate_below_two_chars():
    # "д" is a listed suffix; a 2-char word would drop to 1 char, which the
    # >=2 guard should refuse, so the word is returned unchanged.
    assert light_stem("үд") == "үд"


def test_build_query_variants_includes_original_and_folded():
    variants = build_query_variants("өргөө")
    assert "өргөө" in variants
    assert "оргоо" in variants


def test_build_query_variants_includes_translit_for_latin_input():
    variants = build_query_variants("hool")
    assert "hool" in variants
    assert "хоол" in variants
