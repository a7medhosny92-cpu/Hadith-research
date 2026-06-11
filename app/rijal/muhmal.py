"""Resolve a مهمل narrator (named too briefly to identify — bare «سفيان», «عبد الرحمن») to his
مسمّى (full) form, using the corpus's OWN redundancy — تمييز المهمل بالمسمّى.

The same link «تلميذ ← X ← شيخ» is written bare in one chain and full in another. Where a
(تلميذ, شيخ) context names X **fully and uniquely** somewhere, every *bare* X sitting in that exact
context is that man. Deterministic, corpus-grounded — no grade, no external source. The classical
method the muḥaddithūn used by hand, run over the whole corpus.

Two strengths of context are built (see :func:`build_map`): the exact (تلميذ, شيخ) sandwich, and —
when the exact pair was never seen — the **شيخ-only relaxation**, identifying X by *who he narrates
from* alone («يونس عن الزهري» ⇒ «يونس بن يزيد الأيلي»). Both assert only a *unique* full form; rivals
stay «مشترك». This is «يُميَّز المهمل بشيخه».

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


# The «شيخ-only relaxation»: a bare name is identified by WHO HE NARRATES FROM (his شيخ) alone, for
# when the exact (تلميذ, شيخ) pair was never seen. Its keys carry a «@» sentinel so they can't collide
# with an exact «<prev>\t<next>» key (a folded Arabic prev never starts with «@»).
_RELAX = "@"


def _specific_shaykh(seq: list[str]) -> bool:
    """Is the شيخ named specifically enough to disambiguate by him ALONE? A multi-token name, or a
    single nisba/laqab («الزهري», «الأعمش», «الثوري») — but NOT a bare common ism («محمد», «عمرو»,
    «سفيان»), which names many different teachers and would fuse their unrelated students."""
    return len(seq) >= 2 or (len(seq) == 1 and seq[0].startswith("ال") and len(seq[0]) >= 4)


def _pick_unique(counter: Counter, min_count: int) -> str | None:
    """The **longest clean** single-narrator surface in a context — kept only if it is *unique* at
    that maximal length (rival full forms ⇒ genuine homonymy, left «مشترك») and occurs ≥
    ``min_count``. Returns that surface form, or ``None`` when nothing resolves."""
    by_seq: Counter = Counter()
    surface_of: dict[tuple[str, ...], str] = {}
    for surface, c in counter.items():
        sq = tuple(_seq(surface))
        if _clean(list(sq)):
            by_seq[sq] += c
            surface_of.setdefault(sq, surface)
    if not by_seq:
        return None
    maxlen = max(len(sq) for sq in by_seq)
    if maxlen < 2:                                       # only bare forms here — nothing to resolve TO
        return None
    longest = [sq for sq in by_seq if len(sq) == maxlen]
    if len(longest) != 1 or by_seq[longest[0]] < min_count:
        return None                                      # rival full forms (homonymy) or too rare
    return surface_of[longest[0]]


def build_map(chains: Iterable[list[str]], *, min_count: int = 2) -> dict[str, str]:
    """Map a context → a bare narrator's full surface form there, from the corpus's own redundancy.

    Two key kinds share the one dict (persisted to ``muhmal.json``):

    * **exact** ``"<تلميذ>\\t<شيخ>"`` — the man between this specific (تلميذ, شيخ) sandwich;
    * **شيخ-only** ``"@<bare-ism>\\t<شيخ>"`` — the man cited by ``bare-ism`` who narrates from this
      ``شيخ``, **regardless of his تلميذ** (the «شيخ-only relaxation»), built only when the شيخ is
      :func:`_specific_shaykh`. It resolves «يونس عن الزهري» → «يونس بن يزيد الأيلي» even on a chain
      whose exact (تلميذ, شيخ) pair was never seen.

    Each form is kept via :func:`_pick_unique` (longest, unique at that length — rivals ⇒ homonymy,
    left «مشترك» — and seen ≥ ``min_count``). :func:`resolve` tries the exact key first, then the
    relaxation."""
    exact: dict[tuple[str, str], Counter] = defaultdict(Counter)
    relaxed: dict[tuple[str, str], Counter] = defaultdict(Counter)
    for ch in chains:
        for i in range(1, len(ch) - 1):                  # middle nodes have both a تلميذ and a شيخ
            exact[_ctx_key(ch[i - 1], ch[i + 1])][ch[i]] += 1
            sq, sh = _seq(ch[i]), _seq(ch[i + 1])        # the man, and his شيخ
            if _clean(sq) and _specific_shaykh(sh):
                shaykh = " ".join(sh)
                for blen in (1, 2):                      # index him under each bare run he'd be cited by
                    if blen < len(sq):                   # …only a STRICTLY shorter bare adds specificity
                        relaxed[(" ".join(sq[:blen]), shaykh)][ch[i]] += 1

    out: dict[str, str] = {}
    for (prev, nxt), counter in exact.items():
        full = _pick_unique(counter, min_count)
        if full is not None:
            out[f"{prev}\t{nxt}"] = full
    for (bare, shaykh), counter in relaxed.items():
        full = _pick_unique(counter, min_count)
        if full is not None:
            out[f"{_RELAX}{bare}\t{shaykh}"] = full
    return out


def resolve(name: str, prev: str | None, nxt: str | None, muhmal: dict[str, str]) -> str:
    """The full surface form for a *bare* ``name``, else ``name``.

    Tries the **exact** (تلميذ, شيخ) context first; if that pair was never mapped, falls back to the
    **شيخ-only relaxation** — identify the man by his شيخ alone (``@<bare>\\t<شيخ>``). In both cases the
    bare must be a *leading run* of the resolved full form (so «علي» never becomes «محمد بن جعفر»)."""
    s = _seq(name)
    if not (0 < len(s) <= 2):
        return name                                       # already full (or empty)
    full = muhmal.get("{}\t{}".format(*_ctx_key(prev, nxt)))                  # 1) exact (تلميذ, شيخ)
    if not (full and _seq(full)[: len(s)] == s):                             # 2) else شيخ-only relaxation
        sh = _seq(nxt)
        full = (muhmal.get(f"{_RELAX}{' '.join(s)}\t{' '.join(sh)}")
                if _specific_shaykh(sh) else None)
    return full if full and _seq(full)[: len(s)] == s else name


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
