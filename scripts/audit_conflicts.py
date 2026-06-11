"""Audit the رجال for NARRATOR CONFLICTS — name collisions where a grave verdict (كذاب/متروك/متهم/
وضاع) shares an ism+father with a TRUSTWORTHY narrator, so a bare citation could be graded by the
WRONG man and sink a sound chain (the «كذاب في صحيح مسلم» class).

The complement of ``audit_isnad``/``audit_matn`` but at the RIJAL level, not the chain level: it
finds the homonym clusters that *could* mis-grade, and — crucially — reports whether the matcher
already HOLDS each (ambiguous → «مشترك» / «لا أدري», correct) or DANGEROUSLY resolves to the grave
(a confident, wrong «ضعيف جدًا»). Read-only; run it after any rijal change to catch new collisions.

    python -m scripts.audit_conflicts            # summary + write data/conflicts.json
    python -m scripts.audit_conflicts --cap 50   # keep up to N dangerous cases in the report

A clean run is **DANGEROUS = 0** (every grave↔trustworthy collision is held, not guessed).
"""

from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict

from app.config import get_settings
from app.rijal import RijalIndex, load_entries
from app.rijal.index import _GRAVE, _clean_seq

# Trustworthy categories — a grave namesake colliding with one of these is the dangerous kind.
_TRUST = {"صحابي", "ثقة", "حافظ", "حجة", "صدوق", "لا بأس", "إمام", "امام"}


def _ism_father(name: str) -> str | None:
    """The 2-token leading form «ism + father» — the homonym key a narrator is usually cited by."""
    seq = _clean_seq(name)
    return " ".join(seq[:2]) if len(seq) >= 2 else None


def sweep(rijal: RijalIndex) -> dict:
    """Group every narrator by ism+father, find the grave↔trustworthy collisions, and classify each
    by what ``lookup`` does: ``dangerous`` (confident grave), ``held`` (ambiguous), or ``ok``."""
    groups: dict[str, list] = defaultdict(list)
    for entry in rijal._entries:
        key = _ism_father(entry.name)
        if key:
            groups[key].append(entry)

    dangerous: list[dict] = []
    held = ok = 0
    for key, members in groups.items():
        cats = {m.category for m in members}
        if not ((cats & _GRAVE) and (cats & _TRUST)):
            continue                               # not a grave↔trustworthy collision
        match = rijal.lookup(key)
        if match and match.entry.category in _GRAVE and not match.ambiguous:
            dangerous.append({
                "name": key,
                "grave": match.entry.name,
                "grade": match.entry.category,
                "trustworthy": [m.name for m in members if m.category in _TRUST][:3],
            })
        elif match and match.ambiguous:
            held += 1
        else:
            ok += 1
    return {
        "groups": len(groups),
        "collisions": len(dangerous) + held + ok,
        "dangerous": dangerous,
        "held": held,
        "ok": ok,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Audit the رجال for grave↔trustworthy name conflicts.")
    ap.add_argument("--cap", type=int, default=100, help="dangerous cases to keep in the report")
    args = ap.parse_args()

    settings = get_settings()
    rijal = RijalIndex(load_entries(settings.rijal_file))
    print(f"rijal entries: {rijal.count()}")
    res = sweep(rijal)

    report = {
        "generated": time.strftime("%Y-%m-%d %H:%M"),
        "rijal_entries": rijal.count(),
        "ism_father_groups": res["groups"],
        "collisions": res["collisions"],
        "counts": {"dangerous": len(res["dangerous"]), "held": res["held"], "ok": res["ok"]},
        "dangerous": res["dangerous"][: args.cap],
    }
    out = settings.data_dir / "conflicts.json"
    out.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")

    print(f"grave↔trustworthy collisions: {res['collisions']}")
    print(f"  [!] DANGEROUS (lookup confidently grades the grave — sinks sound chains): {len(res['dangerous'])}")
    print(f"  [·] held (ambiguous → «مشترك», correct): {res['held']}")
    print(f"  [·] ok (resolves to the trustworthy / none): {res['ok']}")
    for d in res["dangerous"][:20]:
        print(f"      «{d['name']}» → [{d['grade']}] {d['grave']}  (real: {d['trustworthy']})")
    print(f"→ {out}")


if __name__ == "__main__":
    main()
