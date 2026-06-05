"""Extract structured hadith records from a downloaded turath book.

A book is a list of pages (``{"pg", "meta": {...}, "text"}``). Hadith boundaries are
marked inline by ``• [N]`` (N in Arabic-Indic digits) and a single hadith may span
several pages, so we scan the page stream and accumulate across page breaks, tracking
the chapter (bab) heading and the starting page/volume for citation.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Iterator

from app.parsing.grading import extract_grade
from app.parsing.html_clean import (
    arabic_digits_to_int,
    clean_body,
    extract_titles,
    remove_footnote_refs,
    split_footnotes,
)
from app.parsing.isnad_matn import split_isnad_matn

# A hadith starts at a "• [N]" bullet. A "* [N]" line is a takhrij/atraf note, not a
# hadith, so we anchor strictly on the bullet.
_HADITH_MARKER = re.compile(r"•\s*\[\s*([\d٠-٩۰-۹]+)\s*\]")


@dataclass(slots=True)
class ParsedHadith:
    book_id: int
    number: int | None
    text: str            # full hadith text (isnad + matn), diacritics preserved
    isnad: str
    matn: str
    matn_confidence: str  # quote | phrase | none
    grade: str | None
    chapter: str | None
    volume: str | None
    page: int | None      # printed page (for citation)
    page_id: int | None   # turath sequential page id

    def to_dict(self) -> dict:
        return asdict(self)


def _finish(book_id: int, cur: dict, default_grade: str | None) -> ParsedHadith:
    text = " ".join(p.strip() for p in cur["parts"] if p.strip()).strip()
    isnad, matn, confidence = split_isnad_matn(text)
    return ParsedHadith(
        book_id=book_id,
        number=cur["number"],
        text=text,
        isnad=isnad,
        matn=matn,
        matn_confidence=confidence,
        grade=extract_grade(text) or default_grade,
        chapter=cur["chapter"],
        volume=cur["volume"],
        page=cur["page"],
        page_id=cur["page_id"],
    )


def iter_hadith(
    book_id: int,
    pages: Iterable[dict],
    *,
    default_grade: str | None = None,
    start_page_id: int | None = None,
) -> Iterator[ParsedHadith]:
    """Yield :class:`ParsedHadith` for every ``• [N]`` unit in the book.

    ``start_page_id`` skips front matter (the editor's muqaddima, which quotes hadith
    out of sequence): pass the page id where the real numbered text begins.
    """
    current: dict | None = None
    chapter: str | None = None

    for page in sorted(pages, key=lambda p: p.get("pg", 0)):
        if start_page_id is not None and page.get("pg", 0) < start_page_id:
            continue
        meta = page.get("meta") or {}
        raw = page.get("text") or ""

        body, _footnotes = split_footnotes(raw)
        titles = extract_titles(body) or (meta.get("headings") or [])
        if titles:
            chapter = remove_footnote_refs(titles[-1]).strip()
        body = clean_body(body)

        matches = list(_HADITH_MARKER.finditer(body))
        if not matches:
            if current is not None:  # whole page continues the open hadith
                current["parts"].append(body)
            continue

        prefix = body[: matches[0].start()]
        if current is not None and prefix.strip():
            current["parts"].append(prefix)

        for i, match in enumerate(matches):
            if current is not None:
                yield _finish(book_id, current, default_grade)
            end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
            current = {
                "number": arabic_digits_to_int(match.group(1)),
                "chapter": chapter,
                "volume": meta.get("vol"),
                "page": meta.get("page"),
                "page_id": page.get("pg"),
                "parts": [body[match.end():end]],
            }

    if current is not None:
        yield _finish(book_id, current, default_grade)


def _first_text_page(data: dict) -> int | None:
    """Page id where the real numbered text starts, from the ``numbers`` index
    (hadith number → page id). Used to skip the editor's muqaddima."""
    numbers = (data.get("indexes") or {}).get("numbers") or {}
    pages = [int(v) for v in numbers.values() if str(v).lstrip("-").isdigit()]
    return min(pages) if pages else None


def parse_book_file(path: str | Path, *, default_grade: str | None = None) -> list[ParsedHadith]:
    """Parse a downloaded ``{raw_dir}/books/{id}.json`` file into hadith records."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return list(
        iter_hadith(
            int(data["book_id"]),
            data.get("pages", []),
            default_grade=default_grade,
            start_page_id=_first_text_page(data),
        )
    )
