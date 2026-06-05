"""Health and ingestion-status endpoints."""

from __future__ import annotations

import json

from fastapi import APIRouter

from app import __version__
from app.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "version": __version__}


@router.get("/health/ingestion")
def ingestion_status() -> dict:
    """Summarise the resumable download manifest, if a crawl has started."""
    manifest_path = get_settings().raw_dir / "manifest.json"
    if not manifest_path.exists():
        return {"started": False, "books": 0}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    books = manifest.get("books", {})
    by_status: dict[str, int] = {}
    pages = 0
    for entry in books.values():
        by_status[entry["status"]] = by_status.get(entry["status"], 0) + 1
        pages += entry.get("pages_fetched", 0)
    return {"started": True, "books": len(books), "pages_fetched": pages, "by_status": by_status}
