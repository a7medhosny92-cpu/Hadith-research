"""The /ask endpoint: answer a question with hadith + scholarly commentary, cited.

Retrieval-grounded and extractive by default (no LLM needed). The hadith index is
shared with /search; the sharh index is provided here (prebuilt sharh_index.db or
built in memory from processed/sharh JSONL).
"""

from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, Depends, Query

from app.config import get_settings
from app.qa import answer_question
from app.routers.search import get_index
from app.search import HadithIndex, SharhIndex

router = APIRouter(tags=["ask"])


@lru_cache(maxsize=1)
def get_sharh_index() -> SharhIndex:
    settings = get_settings()
    if settings.sharh_index_path.exists():
        return SharhIndex(settings.sharh_index_path)
    sharh_dir = settings.processed_dir / "sharh"
    if sharh_dir.exists() and any(sharh_dir.glob("*.jsonl")):
        return SharhIndex.build_from_processed(sharh_dir)
    return SharhIndex()  # empty — answers still work, just without commentary


@router.get("/ask")
def ask(
    q: str = Query(..., min_length=2, description="question in Arabic"),
    k_hadith: int = Query(5, ge=1, le=20),
    k_sharh: int = Query(3, ge=0, le=10),
    hadith_index: HadithIndex = Depends(get_index),
    sharh_index: SharhIndex = Depends(get_sharh_index),
) -> dict:
    return answer_question(
        q, hadith_index, sharh_index, k_hadith=k_hadith, k_sharh=k_sharh
    )
