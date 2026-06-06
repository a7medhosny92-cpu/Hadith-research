"""Tell what a query is about, so a single input can route to the right dossier.

Two kinds for now: a **person** ("من هو فلان", "ترجمة فلان", or a bare known-narrator
name) → the narrator card; otherwise **text** (a hadith or a topic) → the hadith
dossier built on the best match. Keeps the four explicit modes available, but means
the user no longer has to guess which one to pick.
"""

from __future__ import annotations

import re

# "من هو فلان" · "من هي" · "ترجمة فلان" · "أخبرني عن فلان" · "عرّف بفلان" · "الراوي فلان"
_PERSON = re.compile(
    r"^\s*(?:من\s+هو|من\s+هي|من\s+هم|ترجم[ةه]|أخبرني\s+عن|عرّف\s+ب?|الراوي)\s+(.+?)\s*[؟?]?\s*$"
)


def detect_intent(q: str, *, is_known_person=None) -> tuple[str, str]:
    """Return ``(kind, subject)`` where kind is ``"person"`` or ``"text"``.

    ``is_known_person(name)`` (optional) lets a bare short name that the rijal/graph
    recognises be treated as a person too (e.g. just «الزهري»)."""
    q = (q or "").strip()
    m = _PERSON.match(q)
    if m:
        return "person", m.group(1).strip()
    if is_known_person and 1 <= len(q.split()) <= 4 and is_known_person(q):
        return "person", q
    return "text", q
