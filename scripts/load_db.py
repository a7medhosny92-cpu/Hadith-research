"""Load parsed JSONL into PostgreSQL (production store), optionally with embeddings.

    python -m scripts.load_db               # create tables + load hadith & sharh + embed
    python -m scripts.load_db --no-embed    # load text only; backfill vectors later

Requires the production install (psycopg + pgvector) and a reachable DATABASE_URL
(see app.config). The dev path uses scripts.index (sqlite) instead and needs none
of this.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, Iterator

from app.config import get_settings
from app.parsing.normalize import normalize_for_search
from app.search.embeddings import load_embedder
from app.search.index import COLLECTION_NAMES


def _read(path: Path) -> Iterator[dict]:
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def _batched(items: Iterable, size: int) -> Iterator[list]:
    batch: list = []
    for item in items:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def main() -> None:
    parser = argparse.ArgumentParser(description="Load parsed JSONL into PostgreSQL")
    parser.add_argument("--no-embed", action="store_true", help="skip embedding")
    parser.add_argument("--batch", type=int, default=256)
    args = parser.parse_args()

    settings = get_settings()
    # Imported here so the dev install (no pgvector) can still import the app.
    from app.db import get_engine, new_session
    from app.models.tables import Base, Hadith, SharhPassage

    Base.metadata.create_all(get_engine())
    embedder = None if args.no_embed else load_embedder(settings)
    session = new_session()
    processed = settings.processed_dir

    def flush(objects: list, texts: list[str]) -> None:
        if embedder is not None:
            for obj, vec in zip(objects, embedder.embed(texts)):
                obj.embedding = vec
        session.add_all(objects)
        session.commit()

    total_h = 0
    for jsonl in sorted(processed.glob("*.jsonl")):
        for chunk in _batched(_read(jsonl), args.batch):
            objs, texts = [], []
            for r in chunk:
                objs.append(Hadith(
                    book_id=r["book_id"], collection=COLLECTION_NAMES.get(r["book_id"]),
                    number=r.get("number"), matn=r.get("matn") or "",
                    matn_norm=normalize_for_search(r.get("matn") or ""),
                    isnad=r.get("isnad"), grade=r.get("grade"),
                    chapter=r.get("chapter"), page=r.get("page"), volume=r.get("volume"),
                ))
                texts.append(r.get("matn") or "")
            flush(objs, texts)
            total_h += len(objs)
    print(f"loaded {total_h} hadith")

    total_s = 0
    for jsonl in sorted((processed / "sharh").glob("*.jsonl")):
        for chunk in _batched(_read(jsonl), args.batch):
            objs, texts = [], []
            for r in chunk:
                objs.append(SharhPassage(
                    book_id=r["book_id"], sharh_name=r.get("sharh"),
                    base_id=r.get("base_id"), base_name=r.get("base_name"),
                    hadith_number=r.get("hadith_number"), chapter=r.get("chapter"),
                    page=r.get("page"), page_id=r.get("page_id"),
                    text=r.get("text") or "",
                    text_norm=normalize_for_search(r.get("text") or ""),
                ))
                texts.append(r.get("text") or "")
            flush(objs, texts)
            total_s += len(objs)
    print(f"loaded {total_s} sharh passages")
    session.close()


if __name__ == "__main__":
    main()
