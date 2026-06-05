"""Extract commentary (شرح) passages from a downloaded sharh book and link them to
the base collection they explain (so /ask can surface "what the scholars said").

The link granularity depends on what the edition provides, chosen per book:

* **by number** — the sharh carries a ``numbers`` index (hadith number → page),
  e.g. فتح الباري. A hadith's commentary is the page span up to the next number, so
  the passage links to that exact hadith number in the base collection.
* **by chapter** — no ``numbers`` index, e.g. شرح النووي. We split the book by its
  headings (كتاب/باب); passages link at chapter granularity (the sharh follows the
  base collection's chapter order).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterator

from app.ingestion.catalog import COMMENTARIES, CORE_COLLECTIONS
from app.parsing.html_clean import clean_body, extract_titles, split_footnotes

#: sharh book id → the base collection id it explains.
SHARH_TO_BASE: dict[int, int] = {
    sid: base for base, ids in COMMENTARIES.items() for sid in ids
}


@dataclass(slots=True)
class SharhPassage:
    book_id: int             # the sharh book
    sharh: str               # sharh title (identifies the commentator)
    base_id: int | None      # collection it explains
    base_name: str | None
    hadith_number: int | None  # linked hadith number (by-number strategy) or None
    chapter: str | None      # heading (كتاب/باب)
    page: int | None         # printed page (citation)
    page_id: int | None      # turath sequential page id
    text: str                # the commentary passage

    def to_dict(self) -> dict:
        return asdict(self)


def _page_body(page: dict) -> str:
    """Readable commentary text for a page: footnotes split off, markup stripped."""
    body, _ = split_footnotes(page.get("text") or "")
    return clean_body(body)


def _chapter_at(page: dict | None) -> str | None:
    titles = extract_titles((page or {}).get("text") or "")
    return titles[-1].strip() if titles else None


def iter_sharh(
    book_id: int,
    name: str,
    pages: list[dict],
    indexes: dict | None,
    *,
    base_id: int | None = None,
) -> Iterator[SharhPassage]:
    base_id = base_id if base_id is not None else SHARH_TO_BASE.get(book_id)
    base_name = CORE_COLLECTIONS.get(base_id) if base_id else None
    common = dict(book_id=book_id, sharh=name, base_id=base_id, base_name=base_name)

    pages = sorted(pages, key=lambda p: p.get("pg", 0))
    by_pg = {p.get("pg", 0): p for p in pages}
    numbers = (indexes or {}).get("numbers") or {}

    if numbers:
        items = sorted(
            (
                (int(n), int(pg))
                for n, pg in numbers.items()
                if str(pg).lstrip("-").isdigit()
            ),
            key=lambda x: x[1],
        )
        max_pg = max(by_pg) if by_pg else 0
        for i, (number, start) in enumerate(items):
            end = max(start, items[i + 1][1] - 1 if i + 1 < len(items) else max_pg)
            text = " ".join(
                t for pg in range(start, end + 1) if (t := _page_body(by_pg.get(pg, {})))
            ).strip()
            if not text:
                continue
            anchor = by_pg.get(start, {})
            yield SharhPassage(
                **common,
                hadith_number=number,
                chapter=_chapter_at(anchor),
                page=(anchor.get("meta") or {}).get("page"),
                page_id=start,
                text=text,
            )
        return

    # by-chapter: accumulate page bodies under the running heading.
    chapter: str | None = None
    anchor: dict | None = None
    buf: list[str] = []

    def flush() -> Iterator[SharhPassage]:
        text = " ".join(buf).strip()
        if text and anchor is not None:
            yield SharhPassage(
                **common,
                hadith_number=None,
                chapter=chapter,
                page=(anchor.get("meta") or {}).get("page"),
                page_id=anchor.get("pg"),
                text=text,
            )

    for page in pages:
        title = _chapter_at(page)
        if title and buf and title != chapter:
            yield from flush()
            chapter, anchor, buf = None, None, []
        if title:
            chapter = title
        if anchor is None:
            anchor = page
        body = _page_body(page)
        if body:
            buf.append(body)
    yield from flush()


def parse_sharh_file(path: str | Path) -> list[SharhPassage]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return list(
        iter_sharh(
            int(data["book_id"]),
            data.get("name", ""),
            data.get("pages", []),
            data.get("indexes"),
        )
    )
