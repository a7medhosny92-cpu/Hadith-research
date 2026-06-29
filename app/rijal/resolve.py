"""Joint, anchored تمييز المهمل: resolve a chain's ambiguous narrators *together*, by the
DOCUMENTED شيخ/تلميذ relations (تهذيب الكمال / الجرح والتعديل / الثقات), propagating outward
from the links we are already sure of.

The per-narrator lever (`canon._pick`) decides each ambiguous name on its own, from the
flat token company of its raw neighbours — but those neighbours are themselves ambiguous, so
a bare «عبد الله» beside the name carries no signal, and the company that should disambiguate
is itself in conflict. This pass instead:

  * ANCHORS the links we are sure of (the terminal صحابي; any name that resolves uniquely);
  * for an ambiguous link, keeps only the homonyms DOCUMENTED as a تلميذ of its (resolved)
    شيخ and/or a شيخ of its (resolved) تلميذ — a DIRECTIONAL, identity-level constraint, not
    a token overlap with an ambiguous bag;
  * PROPAGATES: a newly-resolved link becomes an anchor for its neighbours, and we iterate to
    a fixpoint, so certainty spreads generation by generation up the isnād (الصحابي → التابعي →
    تابع التابعي → …) — exactly the way the muḥaddithūn read «تمييز المهمل بالنظر إلى شيخه وتلميذه».

It is POSITIVE-evidence only: a homonym documented in the relation is selected; the ABSENCE of
documentation never rejects a candidate (the rijal books' تلاميذ lists are not exhaustive). When
the surviving set is not a single man, the link is left ``None`` for the caller to HOLD
(يُتوقَّف) — we never guess. Power is bounded by network coverage: a man flanked only by bare
names with no documented network stays the honest floor.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from app.rijal.index import _clean_seq

if TYPE_CHECKING:
    from app.rijal.index import RijalEntry


def network_key(name: str) -> str:
    """The order-preserving folded key a man is stored/looked-up under in the network
    (يزيد بن جابر ≠ جابر بن يزيد), matching ``canon._candidates``/``build_graph``."""
    return " ".join(_clean_seq(name))


class DocumentedNetwork:
    """Each man's documented تلاميذ (men who narrated FROM him) as :func:`network_key` sets, from the
    prose rijal sources. Stored ONE-directional — ``students[T]`` = the تلاميذ of T — because the شيخ
    relation is just its mirror: «T is a شيخ of S» ⟺ «S is a تلميذ of T» ⟺ ``S ∈ students[T]``."""

    def __init__(self, students: dict[str, set[str]] | None = None) -> None:
        self._students = students or {}
        # Build inverted index: student → {teachers} for O(1) shuyukh lookup
        self._teachers: dict[str, set[str]] = {}
        for teacher_key, student_set in self._students.items():
            for student_key in student_set:
                if student_key not in self._teachers:
                    self._teachers[student_key] = set()
                self._teachers[student_key].add(teacher_key)

    def is_student_of(self, student_name: str, teacher_name: str) -> bool:
        """Is ``student_name`` recorded as a تلميذ of ``teacher_name``?"""
        return network_key(student_name) in self._students.get(network_key(teacher_name), frozenset())

    def is_teacher_of(self, teacher_name: str, student_name: str) -> bool:
        """Is ``teacher_name`` recorded as a شيخ of ``student_name``? — the mirror of the above."""
        return self.is_student_of(student_name, teacher_name)

    def get_talamidh(self, teacher_name: str) -> set[str]:
        """Return all documented تلاميذ (students) of ``teacher_name`` as canonical names."""
        key = network_key(teacher_name)
        return self._students.get(key, set())

    def get_shuyukh(self, student_name: str) -> set[str]:
        """Return all documented شيوخ (teachers) of ``student_name`` as canonical names.
        Uses the inverted index for O(1) lookup."""
        student_key = network_key(student_name)
        return self._teachers.get(student_key, set())

    def __bool__(self) -> bool:
        return bool(self._students)


def save_network(students: dict[str, set[str]], path: str | Path) -> None:
    """Persist a documented-تلاميذ map (built by ``rijal.tahdhib.documented_students``) to JSON."""
    payload = {"students": {k: sorted(v) for k, v in students.items() if v}}
    Path(path).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def load_network(path: str | Path) -> DocumentedNetwork:
    """Load a persisted documented network; an absent file gives an empty (falsy) network."""
    p = Path(path)
    if not p.exists():
        return DocumentedNetwork()
    data = json.loads(p.read_text(encoding="utf-8"))
    return DocumentedNetwork(students={k: set(v) for k, v in data.get("students", {}).items()})


def resolve_chain(candidates: list[list[str]], anchors: list[str | None],
                  network: DocumentedNetwork,
                  route_starts: frozenset[int] | set[int] = frozenset()) -> list[str | None]:
    """Resolve the ambiguous links of one chain by directional, anchored propagation.

    ``candidates[i]`` — the homonym names for link *i*, in **chain order**: ``[0]`` is the
    collector side (the تلميذ end) and ``[-1]`` is the terminal (الصحابي), each link narrating
    *from* the next (``links[i]`` is the تلميذ of ``links[i+1]``).
    ``anchors[i]`` — a confident name for link *i*, or ``None``.
    ``route_starts`` — indices that BEGIN a new route after a تحويل (ح): the man before such an
    index and the one at it are on different routes, so they are not each other's شيخ/تلميذ.

    Returns ``resolved[i]`` = the chosen name, or ``None`` when the link must be held.
    """
    n = len(candidates)
    resolved: list[str | None] = list(anchors)
    if not network:
        return resolved
    changed = True
    while changed:                       # constraint propagation to a fixpoint
        changed = False
        for i in range(n):
            if resolved[i] or len(candidates[i]) <= 1:
                continue                 # already fixed, or nothing to choose
            # the link below (i+1) is my شيخ — unless it opens a new route (across a ح seam);
            # the link above (i-1) is my تلميذ — unless I open one.
            shaykh = resolved[i + 1] if (i + 1 < n and (i + 1) not in route_starts) else None
            tilmidh = resolved[i - 1] if (i - 1 >= 0 and i not in route_starts) else None
            if not (shaykh or tilmidh):
                continue
            supported = {
                c for c in candidates[i]
                if (shaykh and network.is_student_of(c, shaykh))
                or (tilmidh and network.is_teacher_of(c, tilmidh))
            }
            if len(supported) == 1:      # a single documented fit → resolve; else HOLD
                resolved[i] = next(iter(supported))
                changed = True
    return resolved


def disambiguate_by_context(
    query_name: str,
    candidates: list["RijalEntry"],
    network: "DocumentedNetwork | None",
    chain_context: dict[str, set[str]]
) -> list["RijalEntry"]:
    """
    Use shuyukh/talamidh from the documented network to filter candidates by chain context.

    Args:
        query_name: The ambiguous narrator name being resolved
        candidates: List of RijalEntry candidates from the inverted index
        network: DocumentedNetwork containing shuyukh/talamidh relationships
        chain_context: Dict with 'shuyukh' and 'talamidh' sets of canonical names in the chain

    Returns:
        Filtered list of candidates (max 10) sorted by context overlap score

    Example:
        - Query: "ابن عمر"
        - Context: shuyukh = {"سالم بن عبد الله بن عمر", "نافع بن عبد الرحمن"}
        - Candidates: 339 options
        - Filter: Keep only candidates whose shuyukh/talamidh overlap with context
        - Result: 1-5 candidates instead of 339
    """
    if not network or not candidates:
        return candidates

    context_shuyukh = set(chain_context.get('shuyukh', []))
    context_talamidh = set(chain_context.get('talamidh', []))

    if not context_shuyukh and not context_talamidh:
        return candidates

    scored = []
    for cand in candidates:
        cand_name = cand.name

        # Get shuyukh and talamidh for this candidate from the network
        cand_shuyukh = network.get_shuyukh(cand_name) if network else set()
        cand_talamidh = network.get_talamidh(cand_name) if network else set()

        # Calculate overlap score
        shuyukh_overlap = len(context_shuyukh & cand_shuyukh)
        talamidh_overlap = len(context_talamidh & cand_talamidh)
        total_overlap = shuyukh_overlap + talamidh_overlap

        if total_overlap > 0:
            scored.append((cand, total_overlap, shuyukh_overlap, talamidh_overlap))

    # Sort by total overlap, then by shuyukh overlap (more specific)
    scored.sort(key=lambda x: (x[1], x[2]), reverse=True)

    # Return top 10 by score, or all candidates if no overlap found
    if scored:
        return [cand for cand, score, _, _ in scored[:10]]
    else:
        # No overlap found - return original candidates (fallback)
        return candidates
