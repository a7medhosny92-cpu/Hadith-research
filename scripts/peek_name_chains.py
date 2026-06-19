"""Dump every chain that cites a given narrator surface — read-only, no rebuild.

The proven «زيد بن واقد» method (#270), productised: when a homonym is mis-graded (a W/S case
like «عبد الله بن واقد» → wrongly the متروك الحراني), we write a قاعدة بالشيخ — but the شيخ markers
must come from the REAL chains, never invented (لا نختلق). This finds every isnad whose cited surface
folds-equal to the target and prints, per chain, the **تلميذ → [the name] → شيخ** context and how the
matcher resolved it (surface · resolved · grade), plus an AGGREGATED tally of the شيوخ (the next man on
the route) and تلاميذ (the previous man). The شيوخ tally is exactly the raw material for a قاعدة: a شيخ
that appears only for one homonym is a distinctive marker; a shared one is left held.

    python -m scripts.peek_name_chains "عبد الله بن واقد"
    python -m scripts.peek_name_chains "عبد الله بن واقد" --collection "صحيح مسلم" --show 40
"""

from __future__ import annotations

import argparse
import sqlite3
from collections import Counter

from app.config import get_settings
from app.parsing.normalize import normalize_for_search
from app.qa.isnad import analyze_isnad
from app.rijal import RijalIndex, load_entries
from app.rijal.muhmal import load_map as load_muhmal_map
from app.rijal.resolve import load_network
from scripts.audit_isnad import _build_canon


def _f(s: str) -> str:
    return normalize_for_search(s or "")


def main() -> None:
    ap = argparse.ArgumentParser(description="Dump the chains that cite a narrator surface — read-only.")
    ap.add_argument("name", help="the cited surface to find (folded match, e.g. «عبد الله بن واقد»)")
    ap.add_argument("--collection", default=None, help="filter to one collection")
    ap.add_argument("--limit", type=int, default=None, help="scan only the first N chains")
    ap.add_argument("--show", type=int, default=30, help="how many example chains to print")
    args = ap.parse_args()

    target = _f(args.name)
    settings = get_settings()
    rijal = RijalIndex(load_entries(settings.rijal_file))
    canon = _build_canon(settings, rijal)
    muhmal = load_muhmal_map(settings.data_dir / "muhmal.json")
    network = load_network(settings.documented_network_path)
    print(f"target «{args.name}» (folded: {target})  ·  rijal {rijal.count()}  ·  "
          f"شبكة {'yes' if network else 'no'}")

    if not settings.index_path.exists():
        print(f"⚠ no index at {settings.index_path} — run from the build dir (needs data/index.db).")
        return
    con = sqlite3.connect(str(settings.index_path))
    sql = "SELECT collection, number, isnad FROM hadith WHERE trim(isnad) <> ''"
    rows = con.execute(sql).fetchall()
    con.close()
    if args.limit:
        rows = rows[: args.limit]
    print(f"scanning {len(rows)} chains…", flush=True)

    shaykhs: Counter[str] = Counter()       # the next man on the route (whom he narrates FROM)
    tilmidh: Counter[str] = Counter()       # the previous man (who narrates FROM him)
    grades: Counter[str] = Counter()        # how the matcher graded the position
    resolved_to: Counter[str] = Counter()
    n_hits = 0
    examples: list[str] = []
    for coll, num, isnad in rows:
        if args.collection and coll != args.collection:
            continue
        a = analyze_isnad(isnad, rijal=rijal, canon=canon, muhmal=muhmal, network=network)
        nars = a.narrators
        for i, nar in enumerate(nars):
            if _f(nar.get("name")) != target:
                continue
            n_hits += 1
            sh = nars[i + 1]["name"] if i + 1 < len(nars) else "—(آخر السند)"
            tl = nars[i - 1]["name"] if i - 1 >= 0 else "—(أول السند)"
            shaykhs[sh] += 1
            tilmidh[tl] += 1
            rij = nar.get("rijal")
            g = (rij or {}).get("grade") or ("مشترك" if rij and rij.get("ambiguous") else "غير معروف")
            grades[g] += 1
            if nar.get("resolved"):
                resolved_to[nar["resolved"]] += 1
            if len(examples) < args.show:
                res = f"  →مُيِّز: {nar['resolved']}" if nar.get("resolved") else ""
                examples.append(f"  [{coll}] #{num}  ·  {tl}  →  «{nar['name']}»  →  {sh}   [{g}]{res}")

    print(f"\n=== {n_hits} positions cite «{args.name}»"
          + (f" in {args.collection}" if args.collection else "") + " ===")
    print("\nexamples (تلميذ → [name] → شيخ  ·  [grade]):")
    print("\n".join(examples) if examples else "  (none)")
    print(f"\nالشيوخ (the man AFTER — narrates FROM; the قاعدة marker):")
    for sh, ct in shaykhs.most_common(25):
        print(f"  {ct:4}  {sh}")
    print(f"\nالتلاميذ (the man BEFORE — narrates FROM him):")
    for tl, ct in tilmidh.most_common(15):
        print(f"  {ct:4}  {tl}")
    print(f"\nhow the matcher graded these positions:")
    for g, ct in grades.most_common():
        print(f"  {ct:4}  {g}")
    if resolved_to:
        print(f"\nresolved-to (a lever fired):")
        for r, ct in resolved_to.most_common(10):
            print(f"  {ct:4}  {r}")


if __name__ == "__main__":
    main()
