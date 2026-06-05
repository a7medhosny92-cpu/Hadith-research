"""Async client for the turath.io public API.

Endpoints (reverse-engineered from the turath.io SPA + the public ``turath-sdk``,
all verified live against this environment):

* Catalog : ``GET {files}/data-v3.json``      → ``{cats, books, authors, ...}`` (zstd)
* Book     : ``GET {api}/book?id=&include=indexes&ver=3``
* Page     : ``GET {api}/page?book_id=&pg=&ver=3`` → ``{meta: <json-str>, text}``
* Author   : ``GET {api}/author?id=&ver=3``
* Book file: ``GET {files}/books/{id}.json``   (static dump; often 404 → fall back to pages)

The API is public (no auth) but Cloudflare-fronted. We stay polite: a shared rate
limiter, an honest User-Agent, and exponential backoff on 429/5xx/network errors.
"""

from __future__ import annotations

import asyncio
import json
import random
import time
from typing import Any

import httpx
import zstandard

API_VERSION = 3


class RateLimiter:
    """Serialises requests to at most ``rate_per_sec`` across all coroutines."""

    def __init__(self, rate_per_sec: float) -> None:
        self._min_interval = 1.0 / rate_per_sec if rate_per_sec > 0 else 0.0
        self._lock = asyncio.Lock()
        self._next_allowed = 0.0

    async def acquire(self) -> None:
        if self._min_interval <= 0:
            return
        async with self._lock:
            now = time.monotonic()
            wait = self._next_allowed - now
            if wait > 0:
                await asyncio.sleep(wait)
            self._next_allowed = max(now, self._next_allowed) + self._min_interval


def _loads_maybe_zstd(raw: bytes) -> Any:
    """Parse JSON, transparently handling a zstd-compressed body.

    httpx auto-decodes gzip/deflate/br; the turath catalog is served as ``zstd``
    which httpx may pass through untouched depending on version, so we decode it
    ourselves when a plain JSON parse fails.
    """
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError):
        decompressed = zstandard.ZstdDecompressor().stream_reader(raw)
        return json.loads(decompressed.read())


class TurathClient:
    """Thin async wrapper over the turath.io endpoints with rate limiting + retries."""

    def __init__(
        self,
        api_base: str = "https://api.turath.io",
        files_base: str = "https://files.turath.io",
        *,
        rate_per_sec: float = 4.0,
        max_retries: int = 4,
        timeout: float = 30.0,
        user_agent: str = "HadithResearchBot/0.1",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_base = api_base.rstrip("/")
        self._files_base = files_base.rstrip("/")
        self._max_retries = max_retries
        self._limiter = RateLimiter(rate_per_sec)
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": user_agent, "Accept": "application/json"},
        )

    async def __aenter__(self) -> TurathClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    # ── low-level request with politeness + retry ───────────────────────────
    async def _get(self, url: str, params: dict[str, Any] | None = None) -> httpx.Response:
        last_exc: Exception | None = None
        for attempt in range(self._max_retries + 1):
            await self._limiter.acquire()
            try:
                response = await self._client.get(url, params=params)
            except httpx.TransportError as exc:  # network blip → retry
                last_exc = exc
            else:
                if response.status_code < 400 or response.status_code == 404:
                    return response
                if response.status_code not in (429, 500, 502, 503, 504):
                    response.raise_for_status()
                last_exc = httpx.HTTPStatusError(
                    f"{response.status_code} from {url}", request=response.request,
                    response=response,
                )
                retry_after = _retry_after_seconds(response)
                if retry_after is not None and attempt < self._max_retries:
                    await asyncio.sleep(retry_after)
                    continue
            if attempt < self._max_retries:
                # exponential backoff: 2, 4, 8, 16 (+ jitter)
                await asyncio.sleep(2 ** (attempt + 1) + random.uniform(0, 0.5))
        assert last_exc is not None
        raise last_exc

    # ── public endpoints ─────────────────────────────────────────────────────
    async def get_catalog(self) -> dict[str, Any]:
        """Return the full catalog: ``{cats, books, authors, version, date, ...}``."""
        response = await self._get(f"{self._files_base}/data-v3.json")
        response.raise_for_status()
        return _loads_maybe_zstd(response.content)

    async def get_book_info(self, book_id: int) -> dict[str, Any]:
        """Book metadata + indexes (headings, page maps, hadith→page mapping)."""
        response = await self._get(
            f"{self._api_base}/book",
            params={"id": book_id, "include": "indexes", "ver": API_VERSION},
        )
        response.raise_for_status()
        return response.json()

    async def get_page(self, book_id: int, page: int) -> dict[str, Any] | None:
        """A single page. Returns ``None`` when the page does not exist (book end)."""
        response = await self._get(
            f"{self._api_base}/page",
            params={"book_id": book_id, "pg": page, "ver": API_VERSION},
        )
        response.raise_for_status()
        payload = response.json()
        meta, text = payload.get("meta"), payload.get("text")
        if not meta and not text:
            return None
        return {"meta": json.loads(meta) if isinstance(meta, str) else meta, "text": text or ""}

    async def get_author(self, author_id: int) -> dict[str, Any]:
        response = await self._get(
            f"{self._api_base}/author", params={"id": author_id, "ver": API_VERSION}
        )
        response.raise_for_status()
        return response.json()

    async def get_book_file(self, book_id: int) -> dict[str, Any] | None:
        """Static whole-book dump from the CDN, or ``None`` if not available (404)."""
        response = await self._get(f"{self._files_base}/books/{book_id}.json")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return _loads_maybe_zstd(response.content)


def _retry_after_seconds(response: httpx.Response) -> float | None:
    value = response.headers.get("Retry-After")
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None
