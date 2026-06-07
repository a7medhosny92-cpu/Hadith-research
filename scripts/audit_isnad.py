"""Audit the isnad analysis for likely rijal-matching errors across the whole corpus.

A *heuristic* finder, not a verdict — every hit is for a human to verify. It surfaces
the patterns that betray a wrong narrator match (the kind that flips a sound chain to
«ضعيف جدًا»):

  P  the Prophet ﷺ graded as a narrator                     (should never happen)
  S  «صحابي» on a non-terminal narrator                      (a Companion belongs at the
                                                              chain's end, next to the Prophet)
  W  a fully-named narrator (≥3 tokens) graded متروك/متّهم/كذاب  (usually a homonym mismatch,
                                                              e.g. عثمان بن أبي شيبة ↦ متروك)
  A  an ambiguous match (مشترك)                              (two equally-good namesakes)

Run after building the index + rijal:

    python -m scripts.audit_isnad                # summary + a few examples per flag
    python -m scripts.audit_isnad --examples 40  # more examples
    python -m scripts.audit_isnad --limit 2000   # scan only the first N hadith (faster)
"""

from __future__ import annotations

import argparse
import sqlite3
from collections import Counter

from app.config import get_settings
from app.qa.isnad import analyze_isnad
from app.rijal import RijalIndex, load_entries

_WEAK = {"متروك", "متهم", "كذاب", "وضاع"}          # ranks 0-1: a strong name here is suspect
_TWO_LAST = 2                                       # a صحابي should sit in the last 2 links


def _flag_chain(narrators: list[dict]) -> list[tuple[str, str]]:
    """Return (code, detail) anomalies for one analysed chain."""
    out: list[tuple[str, str]] = []
    n = len(narrators)
    for i, nar in enumerate(narrators):
        rij = nar.get("rijal")
        name = nar.get("name", "")
        if nar.get("is_prophet"):
            if rij:
                out.append(("P", f"الحكم على «{name}» (وهو مصدر الحديث) بـ {rij.get('grade')}"))
            continue
        if not rij:
            continue
        grade = rij.get("grade") or ""
        verdict = rij.get("verdict") or ""
        if grade == "صحابي" and i < n - _TWO_LAST:
            out.append(("S", f"«{name}» (الحلقة {i+1}/{n}) حُكم له «صحابي» وموضعه ليس آخر السند"))
        if any(w in verdict for w in _WEAK) and len(name.split()) >= 3:
            out.append(("W", f"«{name}» (اسمٌ كامل) حُكم له «{verdict}» — يُحتمل خلطٌ باسمٍ مشابه"))
        if rij.get("ambiguous"):
            alts = "، ".join(rij.get("alternatives") or [])
            out.append(("A", f"«{name}» مشترك بين: {rij.get('name')} / {alts}"))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Audit isnad rijal matching for likely errors.")
    ap.add_argument("--limit", type=int, default=None, help="scan only the first N hadith")
    ap.add_argument("--examples", type=int, default=12, help="examples to print per flag")
    args = ap.parse_args()

    settings = get_settings()
    rijal = RijalIndex(load_entries(settings.rijal_file))
    print(f"rijal entries: {rijal.count()}   index: {settings.index_path}\n")
    con = sqlite3.connect(str(settings.index_path))
    sql = "SELECT rowid, collection, number, isnad FROM hadith WHERE trim(isnad) <> ''"
    if args.limit:
        sql += f" LIMIT {args.limit}"

    counts: Counter[str] = Counter()
    examples: dict[str, list[str]] = {"P": [], "S": [], "W": [], "A": []}
    scanned = 0
    for rid, coll, num, isnad in con.execute(sql):
        scanned += 1
        a = analyze_isnad(isnad, rijal=rijal)
        for code, detail in _flag_chain(a.narrators):
            counts[code] += 1
            if len(examples[code]) < args.examples:
                examples[code].append(f"  [{coll} · رقم {num}] {detail}")
    con.close()

    label = {"P": "الحكم على النبيّ ﷺ كراوٍ", "S": "«صحابي» في غير آخر السند",
             "W": "اسمٌ كاملٌ حُكم له بالترك/الكذب (خلطٌ محتمل)", "A": "مطابقةٌ مشتركة (مُلتبسة)"}
    print(f"scanned {scanned} chains\n")
    for code in ("P", "W", "S", "A"):
        print(f"[{code}] {label[code]}: {counts[code]}")
        for ex in examples[code]:
            print(ex)
        print()


if __name__ == "__main__":
    main()
