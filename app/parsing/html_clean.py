"""Clean the turath.io page markup.

turath page ``text`` is lightly marked-up Arabic. Observed structure (verified on
صحيح البخاري ط التأصيل and others):

* ``<span data-type='title' id=toc-82>…</span>``  → chapter/bab heading.
* ``• [١]``                                       → start of a numbered hadith.
* ``(^١)``                                        → inline footnote reference.
* a line of underscores (``_________``)            → separates body from footnotes.
* ``* [١] [التحفة: ع ١٠٦١٢]``                      → takhrij/atraf note (in footnotes).

These helpers are deliberately small and pure so they are easy to test and reuse.
"""

from __future__ import annotations

import re

# ── Arabic-Indic digits ──────────────────────────────────────────────────────
_DIGIT_MAP = {ord(c): str(i) for i, c in enumerate("٠١٢٣٤٥٦٧٨٩")}
_DIGIT_MAP.update({ord(c): str(i) for i, c in enumerate("۰۱۲۳۴۵۶۷۸۹")})  # extended/Persian


def arabic_to_western_digits(text: str) -> str:
    return text.translate(_DIGIT_MAP)


def arabic_digits_to_int(text: str) -> int | None:
    digits = "".join(c for c in arabic_to_western_digits(text) if c.isdigit())
    return int(digits) if digits else None


# ── Diacritic-tolerant matching ──────────────────────────────────────────────
# Arabic combining marks ONLY, built from explicit codepoints so the source stays
# ASCII and the class can never accidentally include the letter block (U+0621–U+064A):
#   U+0610–U+061A  Quranic annotation signs
#   U+064B–U+065F  harakat / tanwin / shadda / sukun (+ extensions)
#   U+0670         dagger (superscript) alef
_MARK_RANGES = ((0x0610, 0x061A), (0x064B, 0x065F), (0x0670, 0x0670))
DIACRITICS_CLASS = "[" + "".join(f"{chr(lo)}-{chr(hi)}" for lo, hi in _MARK_RANGES) + "]"


def flexible_word(word: str) -> str:
    """Regex source matching ``word`` even when diacritised (marks between letters)."""
    marks = DIACRITICS_CLASS + "*"
    return marks.join(re.escape(ch) for ch in word) + marks


# ── Markup helpers ───────────────────────────────────────────────────────────
_TITLE_SPAN = re.compile(
    r"<span[^>]*\bdata-type=['\"]title['\"][^>]*>(.*?)</span>", re.DOTALL
)
_ANY_TAG = re.compile(r"<[^>]+>")
_FOOTNOTE_REF = re.compile(r"\(\^\s*[\d٠-٩۰-۹]+\s*\)")
_FOOTNOTE_SEP = re.compile(r"_{4,}")
_WS = re.compile(r"\s+")


def extract_titles(text: str) -> list[str]:
    """Chapter/bab headings present on the page, in order."""
    return [_WS.sub(" ", m.group(1).strip()) for m in _TITLE_SPAN.finditer(text)]


def remove_title_spans(text: str) -> str:
    return _TITLE_SPAN.sub(" ", text)


def strip_tags(text: str) -> str:
    return _ANY_TAG.sub("", text)


def remove_footnote_refs(text: str) -> str:
    return _FOOTNOTE_REF.sub("", text)


def split_footnotes(text: str) -> tuple[str, str]:
    """Split a page into ``(body, footnotes)`` on the underscore separator.

    The footnotes block holds editorial annotations and takhrij/atraf notes — kept
    out of the hadith text but available for later enrichment.
    """
    match = _FOOTNOTE_SEP.search(text)
    if match:
        return text[: match.start()], text[match.end():]
    return text, ""


def clean_body(text: str) -> str:
    """Body text ready for hadith scanning: headings removed, tags & footnote refs
    gone, whitespace collapsed (diacritics preserved — the matn stays faithful)."""
    text = remove_title_spans(text)
    text = strip_tags(text)
    text = remove_footnote_refs(text)
    return _WS.sub(" ", text).strip()
