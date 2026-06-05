"""Heuristically split a hadith into إسناد (chain) and متن (text).

This is genuinely fuzzy — there is no markup separating the two — so we layer
robust signals and report a confidence. Later phases refine this with narrator
(rijāl) data and external datasets.

Strategy, in order:
  1. ``quote``  — the matn is the first quoted span ("…" / «…»). Strongest signal.
  2. ``phrase`` — split after the *last* speech-introducer (قال/قالت/يقول … :),
                  which normally introduces the matn at the end of the chain.
  3. ``none``   — no reliable boundary; the whole text is treated as isnad.
"""

from __future__ import annotations

import re

from app.parsing.html_clean import flexible_word

_OPEN_QUOTES = ("\"", "«", "“")
_CLOSE_QUOTES = ("\"", "»", "”")
_STRIP = " \t:،.-—\"«»“”"

_INTRO = re.compile(
    r"(?:%s)\s*:" % "|".join(flexible_word(w) for w in ("قال", "قالت", "قالوا", "يقول", "تقول"))
)


def split_isnad_matn(text: str) -> tuple[str, str, str]:
    """Return ``(isnad, matn, confidence)`` where confidence is the strategy used."""
    text = text.strip()

    quote_idx = min((text.find(q) for q in _OPEN_QUOTES if q in text), default=-1)
    if quote_idx != -1:
        # matn runs from the first opening quote to the last closing quote, so trailing
        # footnote/takhrij residue after the final quote is dropped, while multi-quote
        # dialogue hadiths are still captured whole.
        last_close = max((text.rfind(q) for q in _CLOSE_QUOTES), default=-1)
        inner = text[quote_idx + 1:last_close] if last_close > quote_idx else text[quote_idx:]
        isnad = text[:quote_idx].strip(_STRIP)
        return isnad, inner.strip(_STRIP), "quote"

    intros = list(_INTRO.finditer(text))
    if intros:
        cut = intros[-1].end()
        return text[:cut].strip(_STRIP), text[cut:].strip(_STRIP), "phrase"

    return text.strip(_STRIP), "", "none"
