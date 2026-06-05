"""Parse downloaded turath books into structured hadith records (JSONL).

    python -m scripts.parse                 # parse every downloaded book
    python -m scripts.parse --books 1284    # parse specific books

Output: ``{DATA_DIR}/processed/{book_id}.jsonl`` (one hadith per line). This is the
intermediate the indexing/DB-load phase consumes.
"""

from __future__ import annotations

import argparse
import json

from app.config import get_settings
from app.parsing.hadith_extract import parse_book_file

# Collections that are ṣaḥīḥ by scholarly convention — applied when no inline grade
# is found in the text. (Extend as more collections are seeded.)
SAHIH_BY_DEFAULT: dict[int, str] = {1284: "صحيح", 1727: "صحيح"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse downloaded books into hadith JSONL")
    parser.add_argument("--books", type=int, nargs="*", help="book ids (default: all downloaded)")
    args = parser.parse_args()

    settings = get_settings()
    books_dir = settings.raw_dir / "books"
    out_dir = settings.data_dir / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)

    book_ids = args.books or sorted(int(p.stem) for p in books_dir.glob("*.json"))
    if not book_ids:
        print("No downloaded books found. Run `python -m scripts.ingest` first.")
        return

    for book_id in book_ids:
        path = books_dir / f"{book_id}.json"
        if not path.exists():
            print(f"skip {book_id}: not downloaded")
            continue
        hadiths = parse_book_file(path, default_grade=SAHIH_BY_DEFAULT.get(book_id))
        out = out_dir / f"{book_id}.jsonl"
        with out.open("w", encoding="utf-8") as fh:
            for hadith in hadiths:
                fh.write(json.dumps(hadith.to_dict(), ensure_ascii=False) + "\n")
        with_matn = sum(1 for h in hadiths if h.matn)
        print(f"book {book_id}: {len(hadiths)} hadith ({with_matn} with matn) → {out}")


if __name__ == "__main__":
    main()
