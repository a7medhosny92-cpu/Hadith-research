"""Probe الإصابة (9767) for writing its extractor — read-only.

sample_source's boundary segmentation gets stuck in الإصابة's long muqaddima (whose numbered «N-»
lists look like tarjamas), and a «--find» window lands mid-tarjama. So this dumps, in one shot, the
three things isaba_extract needs:

  1) the قسم/حرف structure from indexes.headings (+ inline «القسم الأول..الرابع» markers with context),
     so each tarjama can be mapped to its قسم — I/II → صحابي · III مخضرمون / IV وهم → NOT a Companion;
  2) the first ~90 numbered «N -» heads (muqaddima points first, then the real tarjama heads), so the
     head format (number + name) is visible and the muqaddima/tarjama boundary is found.

Writes `isaba_struct.txt` (clean UTF-8) to upload.

    python -m scripts.peek_isaba
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from app.config import get_settings
from app.parsing.html_clean import clean_block
from app.parsing.rijal_extract import _BOUNDARY

_QISM = re.compile(r"القسم\s+(الأول|الثاني|الثالث|الرابع)")


def main() -> None:
    path = get_settings().raw_dir / "books" / "9767.json"
    if not path.exists():
        print(f"9767.json not found under {path.parent} — make sure الإصابة is downloaded.")
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    lines: list[str] = [f"# الإصابة 9767 — {len(data.get('pages', []))} pages\n"]

    headings = (data.get("indexes") or {}).get("headings") or []
    lines.append(f"=== indexes.headings: {len(headings)} total; the قسم/حرف ones ===")
    for h in headings:
        t = (h.get("title") or "").strip()
        if "قسم" in t or "حرف" in t:
            lines.append(f"  p{h.get('page')!s:>5} L{h.get('level')}  {t[:55]}")

    pages = sorted(data.get("pages", []), key=lambda p: p.get("page", p.get("pg", 0)))
    full = "\n".join(clean_block(p.get("text") or "") for p in pages)

    qism = list(_QISM.finditer(full))
    lines.append(f"\n=== inline «القسم الأول..الرابع» markers: {len(qism)} (first 15, with context) ===")
    for m in qism[:15]:
        ctx = re.sub(r"\s+", " ", full[max(0, m.start() - 35): m.end() + 45])
        lines.append(f"  …{ctx}…")

    bounds = [m for m in _BOUNDARY.finditer(full) if m.group(1) is not None]
    lines.append(f"\n=== {len(bounds)} numbered «N -» heads; first 90 (muqaddima → tarjamas) ===")
    for m in bounds[:90]:
        head = re.sub(r"\s+", " ", full[m.end(): m.end() + 70]).strip()
        lines.append(f"  {m.group(1):>5} | {head[:62]}")

    out = "\n".join(lines)
    Path("isaba_struct.txt").write_text(out, encoding="utf-8")
    print(f"wrote isaba_struct.txt ({len(out)} chars) — upload it")


if __name__ == "__main__":
    main()
