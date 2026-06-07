"""The /sources endpoint: the books the app actually draws on, with their editions.

Lists the curated collections, commentaries (شروح) and rijal sources. The display name
(which carries the edition, e.g. «صحيح البخاري - ط التأصيل») is read cheaply from the
head of each downloaded book file; if a book isn't downloaded yet it falls back to the
curated short name. Dynamic, so the in-app «المنهجية» page stays in sync automatically.
"""

from __future__ import annotations

import re

from fastapi import APIRouter

from app.config import get_settings
from app.ingestion.catalog import ALL_COMMENTARY_IDS, CORE_COLLECTIONS, RIJAL_SOURCES

router = APIRouter(tags=["sources"])

_NAME_RE = re.compile(r'"name"\s*:\s*"([^"]*)"')


def _name(book_id: int, fallback: str) -> str:
    """The book's display name (with edition) from the head of its file — cheap, no full
    JSON load — else the curated fallback / the id."""
    path = get_settings().raw_dir / "books" / f"{book_id}.json"
    if path.exists():
        try:
            with path.open(encoding="utf-8") as fh:
                match = _NAME_RE.search(fh.read(2000))
            if match:
                return match.group(1)
        except OSError:
            pass
    return fallback or f"#{book_id}"


def _entries(ids, names: dict[int, str] | None = None) -> list[dict]:
    names = names or {}
    return [{"id": i, "name": _name(i, names.get(i, ""))} for i in ids]


@router.get("/sources")
def sources() -> dict:
    """The collections, commentaries and rijal sources the app uses, with editions."""
    return {
        "collections": _entries(CORE_COLLECTIONS, CORE_COLLECTIONS),
        "commentaries": _entries(ALL_COMMENTARY_IDS),
        "rijal": _entries(RIJAL_SOURCES, RIJAL_SOURCES),
    }
