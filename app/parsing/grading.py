"""Detect an explicit authenticity grade (حكم) in hadith text.

Many editions (e.g. al-Albānī, al-Arnaʾūṭ) print a ruling next to the hadith:
``إسناده صحيح``, ``حديث حسن صحيح``, ``[ضعيف]``, ``قال الترمذي: حسن`` …

We only match a grade when it sits in a *grading context* (after إسناد/حديث/حكم,
a ``قال …:`` attribution, or in brackets) to avoid matching the word صحيح where it
merely occurs in the matn. Returns the normalised grade or ``None``.
"""

from __future__ import annotations

import re

from app.parsing.html_clean import DIACRITICS_CLASS, flexible_word

# Order matters: longer / more specific grades first.
_GRADES = ["حسن صحيح", "صحيح لغيره", "حسن لغيره", "ضعيف جدا", "صحيح", "حسن", "ضعيف",
           "موضوع", "منكر", "شاذ", "متروك"]
_GRADE_ALT = "|".join(flexible_word(g) for g in _GRADES)

# A grade preceded by a grading-context cue …
_CTX = re.compile(
    r"(?:%s|%s|%s|قال[^:]{0,25}:)\s*[«\"]?(%s)"
    % (flexible_word("إسناده"), flexible_word("حديث"), flexible_word("حكم"), _GRADE_ALT)
)
# … or a bracketed ruling like [صحيح] / (ضعيف).
_BRACKET = re.compile(r"[\[(]\s*(%s)\s*[\])]" % _GRADE_ALT)

_MARKS = re.compile(DIACRITICS_CLASS)
_WS = re.compile(r"\s+")


def extract_grade(text: str) -> str | None:
    for pattern in (_BRACKET, _CTX):
        match = pattern.search(text)
        if match:
            grade = _MARKS.sub("", match.group(1))  # drop diacritics from the match
            return _WS.sub(" ", grade).strip()
    return None
