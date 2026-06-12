"""Probe الثقات ممن لم يقع في الكتب الستة (ابن قطلوبغا, 96165) for writing its extractor — read-only.

Unlike الإصابة (where the قسم heading IS the grade, so headings alone sufficed), الثقات is a PROSE
rijal dictionary: each tarjama's grade signal lives in the BODY — the توثيق by inclusion plus the
cited critics' verdicts («وثقه فلان», «ذكره ابن حبان في الثقات», «قال أبو حاتم: …») — and so does the
شيوخ/تلاميذ network («روى عن… روى عنه…» / the terse «عَن:» / «وعَنه:»). So this dumps, in one shot,
everything the extractor needs to be designed:

  1) `indexes.headings` (count + a sample) — to see whether tarjama heads live there (as in الإصابة)
     or only as numbered «N -» heads in the body;
  2) the numbered-boundary count (rijal_extract._BOUNDARY);
  3) several FULL tarjama bodies — the first few (to find the muqaddima→tarjama boundary) AND a slice
     from the middle (guaranteed-real tarjamas) — so the name / network / verdict / footnote format is
     visible verbatim.

Writes `thiqat_struct.txt` (clean UTF-8) to upload.

    python -m scripts.peek_thiqat
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from app.config import get_settings
from app.parsing.html_clean import clean_block
from app.parsing.rijal_extract import _BOUNDARY

THIQAT_BOOK_ID = 96165
_BODY_CAP = 600          # chars of each tarjama body to dump
_HEAD_SAMPLE = 40        # indexes.headings to list
_FIRST_N = 10            # full bodies from the start (to locate the muqaddima boundary)
_MID_N = 8               # full bodies from the middle (definitely real tarjamas)


def main() -> None:
    path = get_settings().raw_dir / "books" / f"{THIQAT_BOOK_ID}.json"
    if not path.exists():
        print(f"{THIQAT_BOOK_ID}.json not found under {path.parent} — make sure الثقات is downloaded.")
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    lines: list[str] = [f"# الثقات ممن لم يقع في الكتب الستة {THIQAT_BOOK_ID} — "
                        f"{len(data.get('pages', []))} pages\n"]

    headings = (data.get("indexes") or {}).get("headings") or []
    lines.append(f"=== indexes.headings: {len(headings)} total; first {_HEAD_SAMPLE} ===")
    for h in headings[:_HEAD_SAMPLE]:
        t = re.sub(r"\s+", " ", h.get("title") or "").strip()
        lines.append(f"  p{h.get('page')!s:>5} L{h.get('level')}  {t[:60]}")

    pages = sorted(data.get("pages", []), key=lambda p: p.get("page", p.get("pg", 0)))
    full = "\n".join(clean_block(p.get("text") or "") for p in pages)

    bounds = [m for m in _BOUNDARY.finditer(full) if m.group(1) is not None]
    lines.append(f"\n=== {len(bounds)} numbered «N -» heads ===")

    def dump(idx: int) -> None:
        m = bounds[idx]
        end = bounds[idx + 1].start() if idx + 1 < len(bounds) else len(full)
        body = re.sub(r"[ \t]+", " ", full[m.end(): end]).strip()
        lines.append(f"\n── #{m.group(1)} (entry {idx}) ──")
        lines.append(body[:_BODY_CAP])

    lines.append(f"\n========== FIRST {_FIRST_N} bodies (muqaddima → first tarjamas) ==========")
    for i in range(min(_FIRST_N, len(bounds))):
        dump(i)

    mid = len(bounds) // 2
    lines.append(f"\n========== {_MID_N} bodies from the MIDDLE (real tarjamas) ==========")
    for i in range(mid, min(mid + _MID_N, len(bounds))):
        dump(i)

    out = "\n".join(lines)
    Path("thiqat_struct.txt").write_text(out, encoding="utf-8")
    print(f"wrote thiqat_struct.txt ({len(out)} chars) — upload it (Drive `data` folder is fine)")


if __name__ == "__main__":
    main()
