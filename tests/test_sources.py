"""The /sources endpoint lists the curated books (with editions when downloaded)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.ingestion.catalog import ALL_COMMENTARY_IDS, CORE_COLLECTIONS, RIJAL_SOURCES
from app.main import app


def test_sources_lists_the_curated_corpus():
    r = TestClient(app).get("/sources")
    assert r.status_code == 200
    d = r.json()
    assert len(d["collections"]) == len(CORE_COLLECTIONS)
    assert len(d["commentaries"]) == len(ALL_COMMENTARY_IDS)
    assert {b["id"] for b in d["rijal"]} == set(RIJAL_SOURCES)
    # every entry carries an id and a non-empty display name (edition or fallback)
    for group in d.values():
        for book in group:
            assert book["id"] and book["name"]
