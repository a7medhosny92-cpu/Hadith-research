"""Build the lexical search index from parsed JSONL.

    python -m scripts.index     # (re)build {DATA_DIR}/index.db from {DATA_DIR}/processed

The API serves search from this file when present; otherwise it builds an in-memory
index from the JSONL on first request (handy in dev).
"""

from __future__ import annotations

import time

from app.config import get_settings
from app.search import HadithIndex, SharhIndex


def main() -> None:
    settings = get_settings()
    processed = settings.processed_dir
    if not processed.exists() or not any(processed.glob("*.jsonl")):
        print("No parsed JSONL found. Run `python -m scripts.parse` first.")
        return
    settings.data_dir.mkdir(parents=True, exist_ok=True)

    started = time.time()
    if settings.index_path.exists():
        settings.index_path.unlink()
    hadith = HadithIndex.build_from_processed(processed, settings.index_path)
    print(f"Indexed {hadith.count()} hadith → {settings.index_path}")

    if settings.sharh_index_path.exists():
        settings.sharh_index_path.unlink()
    sharh = SharhIndex.build_from_processed(processed / "sharh", settings.sharh_index_path)
    print(f"Indexed {sharh.count()} sharh passages → {settings.sharh_index_path}")
    print(f"Done in {time.time() - started:.1f}s")


if __name__ == "__main__":
    main()
