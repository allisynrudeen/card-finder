"""
Validates that an eBay listing eBay's search returned is ACTUALLY the card
you're pricing it against -- not just something that shares a few keywords.

This exists because of a real bug we caught on the first live run: eBay's
keyword search matched "CJ Rodriguez" against a query meant for "Julio
Rodriguez" (different players), and matched specific Mosaic inserts like
"Stare Masters" and "Straight Fire" against a base Ja Morant Mosaic comp
(different products, different real values). Trusting eBay's search alone
isn't safe enough when real money is on the line.
"""

import re

# Catches "/99", "/25", "/ 5" etc -- the standard way numbered parallels are
# printed. If your comp card ISN'T a numbered parallel, a title with this
# pattern is almost always a different, separately-valued product -- caught
# a "Blue Prizm /99" mismatch on the first live run that no keyword list
# would have anticipated.
NUMBERED_PARALLEL_PATTERN = re.compile(r"/\s?\d{1,4}\b")


def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def title_matches_comp(title: str, player_name: str, grade: str, exclude_keywords: list = None, allow_numbered_parallel: bool = False) -> bool:
    """
    True only if:
      - every word of the player's name appears as a whole word in the title
        (catches "CJ Rodriguez" vs "Julio Rodriguez" -- "julio" must appear)
      - the grade (e.g. "PSA 10") appears in the title
      - none of the exclude_keywords (insert/parallel names that mean it's a
        DIFFERENT product than your comp, e.g. "Stare Masters") appear
      - it isn't a numbered parallel ("/99") unless your comp itself is one
        (allow_numbered_parallel=True)
    """
    if not allow_numbered_parallel and NUMBERED_PARALLEL_PATTERN.search(title):
        return False

    norm_title = _normalize(title)
    title_words = set(norm_title.split())

    player_words = _normalize(player_name).split()
    if not all(word in title_words for word in player_words):
        return False

    norm_grade = _normalize(grade)
    if norm_grade and norm_grade not in norm_title:
        return False

    for bad_word in (exclude_keywords or []):
        if _normalize(bad_word) in norm_title:
            return False

    return True
