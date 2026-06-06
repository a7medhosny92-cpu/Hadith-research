"""Hadith & sharh search: lexical (FTS) + optional semantic (vectors), fused."""

from app.search.hybrid import HybridSearcher, rrf_fuse
from app.search.index import (
    COLLECTION_NAMES,
    HadithIndex,
    SearchHit,
    SharhHit,
    SharhIndex,
)
from app.search.vectors import VectorIndex

__all__ = [
    "HadithIndex",
    "SearchHit",
    "SharhIndex",
    "SharhHit",
    "COLLECTION_NAMES",
    "VectorIndex",
    "HybridSearcher",
    "rrf_fuse",
]
