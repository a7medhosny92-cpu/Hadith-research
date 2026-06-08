"""Feed تهذيب الكمال's narrator network into the graph's homonym disambiguation.

`scripts.build_graph` resolves an ambiguous bare name (سعيد ↦ ابن المسيب vs ابن جبير) by the
**company it keeps**: the candidate whose recorded associates best fit the chain's other narrators
(`app.rijal.canon._pick`). Pass 1 learns that company from the corpus; this module adds al-Mizzī's
**authoritative** company on top — every narrator's quoted شيوخ (روى عن) and تلاميذ (روى عنه).

For each tarjama we resolve the man to his رجال canonical name (so the key matches a candidate the
canonicaliser will weigh) and contribute the cleaned tokens of his شيوخ+تلاميذ. We add only when the
man is identified **unambiguously** in the رجال authority — otherwise we could not safely key it.
"""

from __future__ import annotations

from pathlib import Path

from app.parsing.tahdhib_extract import parse_tahdhib_file
from app.rijal.index import RijalIndex, _clean_tokens

TAHDHIB_BOOK_ID = 3722   # تهذيب الكمال (al-Mizzī)


def tahdhib_associations(records: list[dict], rijal: RijalIndex) -> dict[str, set[str]]:
    """Map each تهذيب narrator's رجال canonical name → the tokens of his شيوخ+تلاميذ.

    Skips a record whose narrator is unknown or ambiguous in the رجال authority (we cannot key
    company onto a name we cannot pin to one man)."""
    assoc: dict[str, set[str]] = {}
    for rec in records:
        name = rec.get("name")
        if not name:
            continue
        match = rijal.lookup(name)
        if match is None or match.score < 1.0 or match.ambiguous:
            continue
        tokens: set[str] = set()
        for who in (*rec.get("shuyukh", ()), *rec.get("talamidh", ())):
            tokens |= set(_clean_tokens(who))
        if tokens:
            assoc.setdefault(match.entry.name, set()).update(tokens)
    return assoc


def load_tahdhib_associations(book_path: str | Path, rijal: RijalIndex) -> dict[str, set[str]]:
    """Parse a downloaded ``{raw_dir}/books/3722.json`` and return its narrator associations."""
    return tahdhib_associations(parse_tahdhib_file(book_path), rijal)
