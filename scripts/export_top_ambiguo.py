"""Estrae i top 10 narratori ambigui con più candidati da audit.json."""

import csv
import json
from collections import Counter
from pathlib import Path

from app.config import get_settings


def main():
    settings = get_settings()
    audit_path = settings.data_dir / "audit.json"
    output_path = settings.data_dir / "top_ambiguo.csv"

    print(f"Reading audit data from {audit_path}...")
    with open(audit_path, encoding="utf-8") as f:
        audit = json.load(f)

    # Extract ambiguous narrator rankings from audit.json
    # Format: a_ranked = [{"name": nm, "count": ct, "candidates": a_cands.get(nm, "")}, ...]
    a_ranked = audit.get("a_ranked", [])
    print(f"Found {len(a_ranked)} ambiguous narrators in audit")

    # Filter out kinship references (أبيه, أبي, جده, أمه, etc.)
    # These are handled by kinship resolution logic, not manual disambiguation
    kinship_refs = {"أبيه", "أبي", "جده", "جدته", "أمه", "أخيه", "أخته", "عمه", "عمته", "خاله", "خالته", "ابنه", "بنته"}
    filtered = [item for item in a_ranked if item["name"] not in kinship_refs]

    # Get top 10 by count (after filtering)
    top_10 = filtered[:10]

    print(f"\nFiltered out {len(a_ranked) - len(filtered)} kinship references")
    print(f"Remaining {len(filtered)} ambiguous narrators")

    print("\n=== TOP 10 NARRATORI AMBIGUI (REAL NAMES) ===")
    print(f"{'Rank':<6} {'Name':<30} {'Count':<10} {'Candidates Preview'}")
    print("-" * 80)

    rows = []
    for rank, item in enumerate(top_10, 1):
        name = item["name"]
        count = item["count"]
        candidates_str = item.get("candidates", "")

        # Extract most frequent grade from candidates string
        # Format: "مشترك بين: X [ثقة], Y [صدوق], Z [ضعيف]..."
        grade_counter = Counter()
        if candidates_str:
            # Parse candidates string to extract grades
            import re
            grades = re.findall(r'\[([^\]]+)\]', candidates_str)
            for grade in grades:
                grade_counter[grade] += 1

        most_frequent_grade = grade_counter.most_common(1)[0][0] if grade_counter else "—"

        print(f"{rank:<6} {name:<30} {count:<10} {most_frequent_grade}")

        rows.append({
            "Rank": rank,
            "Nome": name,
            "Numero_Candidati": count,
            "Grado_Più_Frequente": most_frequent_grade,
            "Candidates_String": candidates_str[:200] + "..." if len(candidates_str) > 200 else candidates_str
        })

    # Write to CSV
    print(f"\nWriting to {output_path}...")
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Rank", "Nome", "Numero_Candidati", "Grado_Più_Frequente", "Candidates_String"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Exported {len(rows)} rows to {output_path}")

    # Additional analysis: get full candidate details for each top narrator
    print("\n=== ANALISI DETTAGLIATA CANDIDATI ===")
    from app.rijal.index import load_entries, RijalIndex

    print("Loading rijal index...")
    entries = list(load_entries(settings.rijal_file))
    rijal = RijalIndex(entries)

    detailed_rows = []
    for item in top_10:
        name = item["name"]
        candidates = rijal.candidates(name, max_results=None)

        print(f"\n{name} ({len(candidates)} candidates):")
        for i, cand in enumerate(candidates[:5], 1):  # Show first 5
            print(f"  {i}. {cand.name} [{cand.category or '—'}] - {cand.grade_text or '—'}")
        if len(candidates) > 5:
            print(f"  ... e altri {len(candidates) - 5} candidati")

        detailed_rows.append({
            "Nome": name,
            "Numero_Candidati": len(candidates),
            "Top_5_Candidates": " | ".join([f"{c.name} [{c.category or '—'}]" for c in candidates[:5]])
        })

    # Write detailed CSV
    detailed_path = settings.data_dir / "top_ambiguo_detailed.csv"
    print(f"\nWriting detailed analysis to {detailed_path}...")
    with open(detailed_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Nome", "Numero_Candidati", "Top_5_Candidates"])
        writer.writeheader()
        writer.writerows(detailed_rows)

    print(f"✅ Exported detailed analysis to {detailed_path}")


if __name__ == "__main__":
    main()
