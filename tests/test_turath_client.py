import json

import httpx
import respx
import zstandard

from app.ingestion.turath_client import TurathClient, _loads_maybe_zstd


def test_loads_maybe_zstd_plain_and_compressed():
    payload = {"cats": {}, "books": {"1": {"id": 1}}}
    assert _loads_maybe_zstd(json.dumps(payload).encode()) == payload
    compressed = zstandard.ZstdCompressor().compress(json.dumps(payload).encode())
    assert _loads_maybe_zstd(compressed) == payload


@respx.mock
async def test_get_page_parses_meta():
    meta = {"page": 1, "vol": "1", "book_name": "صحيح البخاري", "headings": []}
    respx.get("https://api.turath.io/page").mock(
        return_value=httpx.Response(200, json={"meta": json.dumps(meta), "text": "نص"})
    )
    async with TurathClient(rate_per_sec=0) as client:
        page = await client.get_page(1284, 1)
    assert page is not None
    assert page["meta"]["book_name"] == "صحيح البخاري"
    assert page["text"] == "نص"


@respx.mock
async def test_get_page_returns_none_at_book_end():
    respx.get("https://api.turath.io/page").mock(
        return_value=httpx.Response(200, json={"meta": "", "text": ""})
    )
    async with TurathClient(rate_per_sec=0) as client:
        assert await client.get_page(1284, 999999) is None


@respx.mock
async def test_get_book_file_404_returns_none():
    respx.get("https://files.turath.io/books/8540.json").mock(
        return_value=httpx.Response(404)
    )
    async with TurathClient(rate_per_sec=0) as client:
        assert await client.get_book_file(8540) is None


@respx.mock
async def test_get_catalog_handles_zstd_body():
    payload = {"cats": {}, "books": {}, "authors": {}, "version": 3}
    compressed = zstandard.ZstdCompressor().compress(json.dumps(payload).encode())
    respx.get("https://files.turath.io/data-v3.json").mock(
        return_value=httpx.Response(200, content=compressed)
    )
    async with TurathClient(rate_per_sec=0) as client:
        assert await client.get_catalog() == payload


@respx.mock
async def test_get_retries_then_succeeds(monkeypatch):
    import app.ingestion.turath_client as mod

    async def _no_sleep(_seconds):  # don't actually back off in tests
        return None

    monkeypatch.setattr(mod.asyncio, "sleep", _no_sleep)
    route = respx.get("https://api.turath.io/author").mock(
        side_effect=[httpx.Response(503), httpx.Response(200, json={"info": {"name": "x"}})]
    )
    async with TurathClient(rate_per_sec=0, max_retries=2) as client:
        result = await client.get_author(44)
    assert result == {"info": {"name": "x"}}
    assert route.call_count == 2
