"""The /books endpoints — a structural navigator over the corpus (the «الكتب» tab).

Lets the user browse the library by its own structure — a collection → its كتب/أبواب
(chapters) → the hadiths under each — instead of only searching. Reads the same
``index.db`` as ``/search`` (via the shared :func:`get_index` singleton), so it is
available the moment the corpus is built and needs no extra data.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.routers.search import get_index
from app.search import HadithIndex
from app.search.index import COLLECTION_NAMES

router = APIRouter(tags=["books"])


@router.get("/books")
def books(index: HadithIndex = Depends(get_index)) -> dict:
    """Every collection in the corpus, with its hadith count, in parse order."""
    return {"collections": index.collections()}


@router.get("/books/{book_id}/chapters")
def chapters(book_id: int, index: HadithIndex = Depends(get_index)) -> dict:
    """The chapters (كتب/أبواب) of one collection, in book order, each with its hadith count."""
    chs = index.chapters(book_id)
    return {
        "book_id": book_id,
        "collection": COLLECTION_NAMES.get(book_id, str(book_id)),
        "chapters": chs,
        "total": len(chs),
    }


@router.get("/books/{book_id}/hadiths")
def hadiths(
    book_id: int,
    chapter: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    index: HadithIndex = Depends(get_index),
) -> dict:
    """The hadiths under one ``chapter`` of a collection (or the whole book when omitted), paged."""
    hits = index.chapter_hadiths(book_id, chapter, offset=offset, limit=limit)
    return {
        "book_id": book_id,
        "collection": COLLECTION_NAMES.get(book_id, str(book_id)),
        "chapter": chapter,
        "offset": offset,
        "hadiths": [h.to_dict() for h in hits],
        "has_more": len(hits) == limit,
    }
