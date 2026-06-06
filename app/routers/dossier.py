"""The /dossier endpoint: one unified, cross-linked card for a query.

Detects intent — a **person** («من هو فلان», or a bare known name) → the narrator
dossier; otherwise a **hadith/topic** → the full hadith dossier on the best match
(plus related hadith). The single front door to everything: متن · إسناد · تخريج ·
أحكام · شروح · رواة, assembled and attributable. Pass ``hadith_id`` for an exact one.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.qa.dossier import hadith_dossier, narrator_dossier
from app.qa.intent import detect_intent
from app.rijal import RijalIndex
from app.rijal.graph import NarratorGraph
from app.routers.ask import get_sharh_index
from app.routers.search import get_embedder, get_index, get_vectors
from app.routers.verify_isnad import get_graph, get_rijal
from app.search import HadithIndex, HybridSearcher, SharhIndex, VectorIndex
from app.search.embeddings import Embedder

router = APIRouter(tags=["dossier"])


@router.get("/dossier")
def dossier(
    q: str | None = Query(None, min_length=2, description="hadith text, a question, or «من هو فلان»"),
    hadith_id: int | None = Query(None, description="dossier for a specific indexed hadith"),
    index: HadithIndex = Depends(get_index),
    sharh_index: SharhIndex = Depends(get_sharh_index),
    vectors: VectorIndex | None = Depends(get_vectors),
    embedder: Embedder | None = Depends(get_embedder),
    rijal: RijalIndex = Depends(get_rijal),
    graph: NarratorGraph | None = Depends(get_graph),
) -> dict:
    kw = dict(
        hadith_index=index, sharh_index=sharh_index, rijal=rijal,
        graph=graph, vectors=vectors, embedder=embedder,
    )
    if hadith_id is not None:
        hit = index.get(hadith_id)
        if hit is None:
            raise HTTPException(status_code=404, detail="hadith not found")
        return hadith_dossier(hit, **kw)
    if not q:
        raise HTTPException(status_code=422, detail="provide q or hadith_id")

    def known(name: str) -> bool:
        return graph is not None and bool(graph.count()) and graph.resolve(name) is not None

    kind, subject = detect_intent(q, is_known_person=known)
    if kind == "person" and graph is not None:
        person = narrator_dossier(subject, graph, rijal)
        if person is not None:
            return person  # else fall through to a text dossier

    searcher = HybridSearcher(index, vectors, embedder)
    hits = searcher.search(subject, limit=5, mode="hybrid")
    if not hits:
        return {"kind": "empty", "query": q}
    out = hadith_dossier(hits[0], **kw)
    out["query"] = q
    out["related"] = [h.to_dict() for h in hits[1:]]
    return out
