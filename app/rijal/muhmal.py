"""Resolve a مهمل narrator (named too briefly to identify — bare «سفيان», «عبد الرحمن») to his
مسمّى (full) form, using the corpus's OWN redundancy — تمييز المهمل بالمسمّى.

The same link «تلميذ ← X ← شيخ» is written bare in one chain and full in another. Where a
(تلميذ, شيخ) context names X **fully and uniquely** somewhere, every *bare* X sitting in that exact
context is that man. Deterministic, corpus-grounded — no grade, no external source. The classical
method the muḥaddithūn used by hand, run over the whole corpus.

Built from the parsed chains in ``build_graph``; the map (``data/muhmal.json``) is then reused at
verdict time so a مهمل narrator stops being «مشترك».
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

from app.parsing.normalize import fold_kunya, normalize_for_search

_DROP = {"بن", "ابن"}
# Words that mark a parsing artifact, not a name: transmission verbs, matn lead-ins, references.
_NOISE = {normalize_for_search(w) for w in (
    "يحدث", "حدثنا", "حدثني", "أخبرنا", "سمعت", "يقول", "قال", "قالت", "الحديث", "حديث",
    "نحو", "نحوه", "مثله", "فاقتص", "عند", "يعني", "هو", "عن", "أنه", "ذكر", "رفعه", "فذكر",
)}


def _seq(name: str | None) -> list[str]:
    """Folded, ordered name tokens (بن/ابن dropped) — the form contexts and names are matched in."""
    return [t for t in fold_kunya(normalize_for_search(name or "").split()) if t and t not in _DROP]


def _clean(seq: list[str]) -> bool:
    """A real single-narrator name token-run: no noise/verb, no «وفلان» conjunction (a second
    narrator), no stray digit (a footnote ref), at most 5 tokens."""
    return (
        0 < len(seq) <= 5
        and not any(t in _NOISE for t in seq)
        and not any(t.startswith("و") and len(t) >= 3 for t in seq[1:])
        and not any(t.isdigit() for t in seq)
    )


def _ctx_key(prev: str | None, nxt: str | None) -> tuple[str, str]:
    return (" ".join(_seq(prev)), " ".join(_seq(nxt)))


def build_map(chains: Iterable[list[str]], *, min_count: int = 2) -> dict[str, str]:
    """Map a «(تلميذ, شيخ)» context (``"<prev>\\t<next>"``) → the narrator's full surface form there.

    For each context we take the **longest clean** name form seen; we keep it only if it is the
    *unique* form at that maximal length (rival full forms ⇒ genuine homonymy, left «مشترك») and it
    occurs at least ``min_count`` times. Bare forms then resolve to it via :func:`resolve`."""
    forms: dict[tuple[str, str], Counter] = defaultdict(Counter)
    for ch in chains:
        for i in range(1, len(ch) - 1):                  # middle nodes have both a تلميذ and a شيخ
            forms[_ctx_key(ch[i - 1], ch[i + 1])][ch[i]] += 1

    out: dict[str, str] = {}
    for key, counter in forms.items():
        by_seq: Counter = Counter()
        surface_of: dict[tuple[str, ...], str] = {}
        for surface, c in counter.items():
            sq = tuple(_seq(surface))
            if _clean(list(sq)):
                by_seq[sq] += c
                surface_of.setdefault(sq, surface)
        if not by_seq:
            continue
        maxlen = max(len(sq) for sq in by_seq)
        if maxlen < 2:                                   # only bare forms here — nothing to resolve TO
            continue
        longest = [sq for sq in by_seq if len(sq) == maxlen]
        if len(longest) != 1 or by_seq[longest[0]] < min_count:
            continue                                     # rival full forms (homonymy) or too rare
        out[f"{key[0]}\t{key[1]}"] = surface_of[longest[0]]
    return out


def resolve(name: str, prev: str | None, nxt: str | None, muhmal: dict[str, str]) -> str:
    """The full surface form for a *bare* ``name`` in the (prev, next) context, else ``name``."""
    s = _seq(name)
    if not (0 < len(s) <= 2):
        return name                                       # already full (or empty)
    full = muhmal.get("{}\t{}".format(*_ctx_key(prev, nxt)))
    if full and _seq(full)[: len(s)] == s:                # the bare must be a leading run of the full
        return full
    return name


def resolve_chain(names: list[str], muhmal: dict[str, str]) -> list[str]:
    """A copy of ``names`` with every bare middle narrator resolved to its full form."""
    if not muhmal or len(names) < 3:
        return names
    return [
        resolve(nm, names[i - 1], names[i + 1], muhmal) if 0 < i < len(names) - 1 else nm
        for i, nm in enumerate(names)
    ]


def load_map(path: str | Path) -> dict[str, str]:
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def save_map(muhmal: dict[str, str], path: str | Path) -> None:
    Path(path).write_text(json.dumps(muhmal, ensure_ascii=False), encoding="utf-8")
