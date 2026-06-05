"""Build / validate a full رجال (narrator) JSONL for /verify-isnad.

The bundled seed (``app/rijal/seed.jsonl``) covers the famous narrators. To grade
more, supply a structured narrator dataset as JSONL and merge it with the seed:

    python -m scripts.build_rijal --input narrators.jsonl --output data/rijal.jsonl
    # then set RIJAL_PATH=data/rijal.jsonl

Each input line:

    {"name": "...", "aliases": ["..."], "kunya": "...",
     "grade": "<verdict text, e.g. ثقة حافظ / صدوق يهم / متروك>",
     "death_year": 198, "source": "..."}

``grade`` is the critic's verdict text; app.rijal.grades classifies it into a
category/rank. This script validates the schema, reports the grade distribution,
and writes the merged file. (Parsing the رجال biographies out of turath cat-26 is a
separate effort; this is the handoff point once a structured dataset exists.)
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from app.rijal.grades import classify
from app.rijal.index import load_seed


def main() -> None:
    parser = argparse.ArgumentParser(description="Build/validate a رجال JSONL")
    parser.add_argument("--input", type=Path, help="narrator JSONL to validate and merge")
    parser.add_argument("--output", type=Path, default=Path("data/rijal.jsonl"))
    parser.add_argument("--no-seed", action="store_true", help="exclude the bundled seed")
    args = parser.parse_args()

    entries: list[dict] = [] if args.no_seed else load_seed()
    if args.input:
        for lineno, line in enumerate(args.input.read_text(encoding="utf-8").splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if "name" not in record or "grade" not in record:
                sys.exit(f"line {lineno}: each record needs 'name' and 'grade'")
            entries.append(record)

    distribution = Counter(classify(e.get("grade") or "")[0] for e in entries)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as fh:
        for entry in entries:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"wrote {len(entries)} narrators → {args.output}")
    for category, count in distribution.most_common():
        print(f"  {category}: {count}")


if __name__ == "__main__":
    main()
