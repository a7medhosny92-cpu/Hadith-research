"""Resumable, polite downloader for the turath.io corpus.

Strategy (validated against the live API):

* The CDN whole-book dump (``/books/{id}.json``) is usually 404, so we download
  **page by page** via ``/page`` — the reliable path — and assemble one JSON file
  per book under ``{raw_dir}/books/{id}.json``.
* Progress is tracked in ``{raw_dir}/manifest.json`` so an interrupted run resumes
  exactly where it stopped (important: the full hadith corpus is ~2.9M pages).
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Iterable

from app.ingestion.catalog import BookRecord
from app.ingestion.turath_client import TurathClient

ProgressHook = Callable[[str], None]


@dataclass
class BookProgress:
    book_id: int
    name: str
    page_count: int
    pages_fetched: int = 0
    status: str = "pending"  # pending | partial | complete | error
    updated_at: float = 0.0
    error: str | None = None


@dataclass
class Manifest:
    """Persisted per-book download state for resumability."""

    path: Path
    books: dict[int, BookProgress] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> "Manifest":
        if path.exists():
            raw = json.loads(path.read_text(encoding="utf-8"))
            books = {int(k): BookProgress(**v) for k, v in raw.get("books", {}).items()}
            return cls(path=path, books=books)
        return cls(path=path)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"books": {str(k): asdict(v) for k, v in self.books.items()}}
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)


class CorpusDownloader:
    def __init__(
        self,
        client: TurathClient,
        raw_dir: Path,
        *,
        save_every: int = 50,
        on_progress: ProgressHook | None = None,
    ) -> None:
        self._client = client
        self._raw_dir = raw_dir
        self._books_dir = raw_dir / "books"
        self._save_every = save_every
        self._on_progress = on_progress or (lambda _msg: None)
        self._manifest = Manifest.load(raw_dir / "manifest.json")
        self._info_by_book: dict[int, dict] = {}

    def _book_path(self, book_id: int) -> Path:
        return self._books_dir / f"{book_id}.json"

    async def download_catalog(self) -> dict:
        """Fetch and cache the catalog; returns the raw catalog dict."""
        catalog = await self._client.get_catalog()
        self._raw_dir.mkdir(parents=True, exist_ok=True)
        (self._raw_dir / "catalog.json").write_text(
            json.dumps(catalog, ensure_ascii=False), encoding="utf-8"
        )
        return catalog

    async def download_books(
        self, books: Iterable[BookRecord], *, max_pages_per_book: int | None = None
    ) -> Manifest:
        """Download (or resume) each book. ``max_pages_per_book`` caps pages — handy
        for smoke tests; leave ``None`` for a full crawl."""
        self._books_dir.mkdir(parents=True, exist_ok=True)
        for book in books:
            await self._download_book(book, max_pages=max_pages_per_book)
        self._manifest.save()
        return self._manifest

    async def _download_book(self, book: BookRecord, *, max_pages: int | None) -> None:
        progress = self._manifest.books.get(book.id) or BookProgress(
            book_id=book.id, name=book.name, page_count=book.page_count
        )
        self._manifest.books[book.id] = progress

        # Book metadata + indexes (headings, hadith-number → page map) are needed for
        # numbering, chapter mapping and skipping front matter. Best-effort, fetched once.
        if book.id not in self._info_by_book:
            try:
                self._info_by_book[book.id] = await self._client.get_book_info(book.id)
            except Exception:  # noqa: BLE001
                self._info_by_book[book.id] = {}

        existing_pages = self._load_existing_pages(book.id)
        start_page = len(existing_pages) + 1
        last_page = book.page_count or (max_pages or 0)
        if max_pages is not None:
            last_page = min(last_page or max_pages, max_pages)

        if start_page > last_page and progress.status == "complete":
            self._write_pages(book, existing_pages)  # ensure meta/indexes are persisted
            self._on_progress(f"skip {book.id} ({book.name}) — already complete")
            return

        self._on_progress(
            f"download {book.id} ({book.name}) pages {start_page}…{last_page}"
        )
        pages = existing_pages
        try:
            for pg in range(start_page, last_page + 1):
                page = await self._client.get_page(book.id, pg)
                if page is None:  # reached the real end of the book
                    break
                pages.append({"pg": pg, **page})
                progress.pages_fetched = len(pages)
                progress.status = "partial"
                progress.updated_at = time.time()
                if pg % self._save_every == 0:
                    self._write_pages(book, pages)
                    self._manifest.save()
            self._write_pages(book, pages)
            complete = max_pages is None or len(pages) >= last_page
            progress.status = "complete" if complete else "partial"
            progress.error = None
        except Exception as exc:  # noqa: BLE001 — record and move on; run is resumable
            progress.status = "error"
            progress.error = repr(exc)
            self._write_pages(book, pages)
            self._manifest.save()
            self._on_progress(f"error {book.id}: {exc!r}")
            return
        progress.updated_at = time.time()
        self._manifest.save()

    def _load_existing_pages(self, book_id: int) -> list[dict]:
        path = self._book_path(book_id)
        if not path.exists():
            return []
        try:
            return json.loads(path.read_text(encoding="utf-8")).get("pages", [])
        except (json.JSONDecodeError, OSError):
            return []

    def _write_pages(self, book: BookRecord, pages: list[dict]) -> None:
        info = self._info_by_book.get(book.id, {})
        payload = {
            "book_id": book.id,
            "name": book.name,
            "author_id": book.author_id,
            "cat_id": book.cat_id,
            "page_count": book.page_count,
            "source": "turath.io",
            "meta": info.get("meta"),
            "indexes": info.get("indexes"),
            "pages": pages,
        }
        path = self._book_path(book.id)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)
