"""Inspect a شرح book's structure — to see why it segments into few/many passages. Read-only.

The sharh navigator splits **by number** (a ``numbers`` index → per-hadith) or, lacking it, **by
chapter** (``<span data-type='title'>`` headings). A book like الفتح الرباني (124910) marks its بابs
as inline parenthetical text «(باب …)», NOT as title spans, so the by-chapter split sees only the
~66 كتاب-level spans → 66 huge passages. This dumps the signals so we can pick a finer split:

  * has a ``numbers`` index? (→ by-number, per hadith)
  * how many title-span headings (the current by-chapter granularity), with samples
  * how often «باب»/«كتاب» appear as INLINE text (a potential finer split point)
  * a sample of raw page text, so we see exactly how بابs are encoded

    python -m scripts.peek_sharh 124910            # الفتح الرباني
    python -m scripts.peek_sharh 124910 --pages 7-9
"""

from __future__ import annotations

import argparse
import json
import re

from app.config import get_settings
from app.parsing.html_clean import clean_body, extract_titles, split_footnotes

_BAB_INLINE = re.compile(r"\(\s*(?:باب|كتاب|قسم|فصل)\b[^)]{0,60}\)")   # «(باب …)» style headings in the body


def main() -> None:
    ap = argparse.ArgumentParser(description="Inspect a شرح book's segmentation signals (read-only).")
    ap.add_argument("book_id", type=int)
    ap.add_argument("--pages", default="", help="raw-text sample, e.g. 7-9 (default: the first 2 content pages)")
    args = ap.parse_args()

    path = get_settings().raw_dir / "books" / f"{args.book_id}.json"
    if not path.exists():
        raise SystemExit(f"{path} not found — the raw turath book isn't downloaded")
    data = json.loads(path.read_text(encoding="utf-8"))
    pages = sorted(data.get("pages", []), key=lambda p: p.get("pg", 0))
    numbers = (data.get("indexes") or {}).get("numbers") or {}

    span_titles, inline_heads = [], 0
    for p in pages:
        t = p.get("text") or ""
        span_titles += extract_titles(t)
        inline_heads += len(_BAB_INLINE.findall(clean_body(split_footnotes(t)[0])))

    print(f"شرح {args.book_id}: {data.get('name','')!r}")
    print(f"  pages: {len(pages)} · numbers index: {len(numbers)} "
          f"({'BY-NUMBER (per hadith)' if numbers else 'BY-CHAPTER (title spans)'})")
    print(f"  title-span headings: {len(span_titles)}  ← the current by-chapter passage count")
    print(f"  inline «(باب/كتاب/قسم …)» in the body text: {inline_heads}  ← a potential finer split")
    print("\n  first title spans:")
    for t in span_titles[:25]:
        print(f"    · {t}")

    if args.pages:
        a, _, b = args.pages.partition("-")
        lo, hi = int(a), int(b or a)
        sample = [p for p in pages if lo <= p.get("pg", 0) <= hi]
    else:
        start = min((int(v) for v in numbers.values() if str(v).lstrip("-").isdigit()), default=0)
        sample = [p for p in pages if p.get("pg", 0) >= start][:2]
    print(f"\n  ── raw text sample ({len(sample)} page(s)) ──")
    for p in sample:
        body = clean_body(split_footnotes(p.get("text") or "")[0])
        print(f"\n  [pg {p.get('pg')} · ص {(p.get('meta') or {}).get('page')}] {body[:1600]}")


if __name__ == "__main__":
    main()
