"""Tests for isnad structural analysis (/verify-isnad)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.qa.isnad import analyze_isnad
from app.routers.search import get_index
from app.search import HadithIndex

CHAIN = (
    "حدثنا الحميدي، حدثنا سفيان، حدثنا يحيى بن سعيد، "
    "عن محمد بن إبراهيم، عن علقمة بن وقاص، عن عمر بن الخطاب"
)


def test_parses_narrators_and_modes():
    a = analyze_isnad(CHAIN)
    names = [n["name"] for n in a.narrators]
    assert a.length == 6
    assert "سفيان" in names
    assert any("يحيى" in n for n in names)
    assert a.modes == {"سماع": 3, "عنعنة": 3}
    assert a.has_anana and not a.has_tahwil


def test_detects_tahwil_with_waw_connectors():
    a = analyze_isnad("حدثنا أبو بكر، حدثنا غندر، عن شعبة ح وحدثنا محمد، عن منصور")
    assert a.has_tahwil
    # the waw-prefixed connector is recognised, so محمد is its own narrator
    assert any(n["name"] == "محمد" for n in a.narrators)


def test_reaches_prophet():
    assert analyze_isnad("حدثنا فلان، عن أنس، عن النبي صلى الله عليه وسلم").reaches_prophet
    assert not analyze_isnad("حدثنا فلان، عن أنس").reaches_prophet


# ── API ─────────────────────────────────────────────────────────────────────
@pytest.fixture
def client() -> TestClient:
    idx = HadithIndex()
    idx.add([{
        "book_id": 1284, "number": 1, "matn": "إنما الأعمال بالنيات",
        "isnad": CHAIN, "grade": "صحيح", "chapter": "بدء الوحي", "page": 179, "volume": "1",
    }])
    app.dependency_overrides[get_index] = lambda: idx
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_api_verify_by_text(client):
    r = client.get("/verify-isnad", params={"isnad": CHAIN})
    assert r.status_code == 200
    assert r.json()["analysis"]["length"] == 6


def test_api_verify_by_hadith_id(client):
    hid = client.get("/search", params={"q": "الأعمال"}).json()["results"][0]["id"]
    body = client.get("/verify-isnad", params={"hadith_id": hid}).json()
    assert body["analysis"]["modes"]["عنعنة"] == 3


def test_api_verify_requires_input(client):
    assert client.get("/verify-isnad").status_code == 422
    assert client.get("/verify-isnad", params={"hadith_id": 999999}).status_code == 404
