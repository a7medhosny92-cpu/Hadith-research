"""Tests for the unified dossier (intent routing + composed cards)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.qa.intent import detect_intent
from app.rijal.graph import NarratorGraph
from app.routers.ask import get_sharh_index
from app.routers.search import get_embedder, get_index, get_vectors
from app.routers.verify_isnad import get_graph
from app.search import HadithIndex, SharhIndex

H = {
    "book_id": 1284, "number": 1, "matn": "إنما الأعمال بالنيات",
    "isnad": "حدثنا الحميدي حدثنا سفيان عن أبي هريرة عن النبي",
    "grade": "صحيح", "chapter": "بدء الوحي", "page": 1, "volume": "1",
}


# ── intent ──────────────────────────────────────────────────────────────────────
def test_intent_person_vs_text():
    assert detect_intent("من هو أبو بكر") == ("person", "أبو بكر")
    assert detect_intent("ترجمة الزهري") == ("person", "الزهري")
    assert detect_intent("إنما الأعمال بالنيات")[0] == "text"


def test_intent_bare_known_name():
    known = lambda n: n == "الزهري"   # only a real known narrator counts
    assert detect_intent("الزهري", is_known_person=known) == ("person", "الزهري")
    assert detect_intent("إنما الأعمال بالنيات", is_known_person=known)[0] == "text"


# ── endpoint ────────────────────────────────────────────────────────────────────
@pytest.fixture
def client():
    idx = HadithIndex(); idx.add([H])
    graph = NarratorGraph(); graph.add_chain(["الحميدي", "سفيان", "أبو هريرة", "النبي"]); graph.commit()
    app.dependency_overrides[get_index] = lambda: idx
    app.dependency_overrides[get_sharh_index] = lambda: SharhIndex()
    app.dependency_overrides[get_graph] = lambda: graph
    app.dependency_overrides[get_vectors] = lambda: None
    app.dependency_overrides[get_embedder] = lambda: None
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_dossier_for_hadith_id_has_all_sections(client):
    hid = client.get("/search", params={"q": "الأعمال بالنيات"}).json()["results"][0]["id"]
    body = client.get("/dossier", params={"hadith_id": hid}).json()
    assert body["kind"] == "hadith"
    for section in ("hadith", "isnad", "takhrij", "rulings", "sharh", "narrators"):
        assert section in body
    assert any(n["name"] for n in body["narrators"])     # chain narrators as chips


def test_dossier_text_query_builds_hadith_card(client):
    body = client.get("/dossier", params={"q": "الأعمال بالنيات"}).json()
    assert body["kind"] == "hadith" and "related" in body


def test_dossier_routes_person(client):
    body = client.get("/dossier", params={"q": "من هو أبو هريرة"}).json()
    assert body["kind"] == "person" and "summary" in body
