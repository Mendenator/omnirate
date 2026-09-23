"""Mongolian-language search preprocessing (S-05).

OpenSearch has no built-in Mongolian analyzer, so folding/translit/stemming
happen in Python at index time (writing `name_folded`/`name_translit`) and at
query time (expanding the user's query into an OR of variants) — see
app/search/client.py for the field mapping these functions feed, and
app/workers/indexer.py for where they're called on write.

K14 acceptance: galig/folding recall >=95% on a 300-query test set.
"""

import re

# ö/ü folding + ё normalization (SOW §5.3): flattens the vowels a Mongolian
# keyboard layout or a typo commonly drops, without discarding the base word.
_FOLD_MAP = str.maketrans({"ө": "о", "Ө": "О", "ү": "у", "Ү": "У", "ё": "е", "Ё": "Е"})


def fold_vowels(text: str) -> str:
    return text.translate(_FOLD_MAP)


# Latin -> Cyrillic transliteration fragments, longest-match-first so digraphs
# (kh, ts, sh, ch, yo, ii) don't get shadowed by their single-letter prefixes.
_TRANSLIT_RULES: list[tuple[str, str]] = [
    ("yo", "ё"),
    ("kh", "х"),
    ("ts", "ц"),
    ("ch", "ч"),
    ("sh", "ш"),
    ("shch", "щ"),
    ("yu", "ю"),
    ("ya", "я"),
    ("ii", "ий"),
    ("uu", "уу"),
    ("oo", "оо"),
    ("u", "ү"),
    ("o", "ө"),
    ("a", "а"),
    ("b", "б"),
    ("v", "в"),
    ("g", "г"),
    ("d", "д"),
    ("e", "э"),
    ("z", "з"),
    ("i", "и"),
    ("k", "к"),
    ("l", "л"),
    ("m", "м"),
    ("n", "н"),
    ("p", "п"),
    ("r", "р"),
    ("s", "с"),
    ("t", "т"),
    ("f", "ф"),
    ("h", "х"),
    ("w", "в"),
    ("y", "й"),
    ("j", "ж"),
    ("c", "к"),
]
_TRANSLIT_RULES.sort(key=lambda rule: -len(rule[0]))


def transliterate_latin_to_cyrillic(latin_text: str) -> str:
    """Best-effort galig conversion for a latin-typed query, e.g. 'hool' -> 'хоол'.

    KNOWN GAP: latin 'u' and the 'oo' digraph are genuinely ambiguous in
    Mongolian romanization — 'u' can stand for у/ү/ө and 'oo' for оо/өө
    depending on the specific word, with no way to disambiguate from the
    latin spelling alone. This function picks one deterministic mapping
    (u->ү, oo->оо), so it does NOT reproduce the SOW's own worked example
    ("urgoo" -> "өргөө", which needs u->ө and oo->өө for that specific
    word) — see tests/test_mongolian_text.py. A correct fix generates
    multiple candidate variants per ambiguous vowel and lets the caller
    (build_query_variants) OR them together, matching what SOW §5.3
    actually describes ("кирилл хувилбарууд руу хөрвүүлж, OR асуулга
    үүсгэнэ" — convert to Cyrillic *variants*, plural). Not yet
    implemented; tracked in docs/PROGRESS.md.
    """
    text = latin_text.lower()
    out = []
    i = 0
    while i < len(text):
        for latin, cyr in _TRANSLIT_RULES:
            if text.startswith(latin, i):
                out.append(cyr)
                i += len(latin)
                break
        else:
            out.append(text[i])  # non-alphabetic char (digits, punctuation) passes through
            i += 1
    return "".join(out)


def is_latin_query(text: str) -> bool:
    return bool(re.fullmatch(r"[a-zA-Z0-9\s'-]+", text.strip())) and bool(text.strip())


# Common Mongolian noun/adjective suffixes (SOW §5.3), longest-first so e.g.
# "-ээс" doesn't get shadowed by a shorter false match.
_SUFFIXES = sorted(
    ["ын", "ийн", "ний", "д", "т", "аас", "ээс", "оос", "өөс", "тай", "тэй", "той"],
    key=len,
    reverse=True,
)


def light_stem(word: str) -> str:
    """Strips at most one trailing suffix, and only when the remaining stem
    is still long enough to be meaningful — avoids "amputating" short words
    like "тэд" down to nothing.
    """
    for suffix in _SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 2:
            return word[: -len(suffix)]
    return word


def build_name_folded(name: str) -> str:
    return fold_vowels(name)


def build_query_variants(query: str) -> list[str]:
    """All forms to OR together at query time: as-typed, vowel-folded, and
    (if the query looks latin) transliterated to Cyrillic."""
    variants = {query, fold_vowels(query)}
    if is_latin_query(query):
        variants.add(transliterate_latin_to_cyrillic(query))
    return list(variants)
