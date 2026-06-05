"""Structural analysis of an isnad (chain of narrators).

We parse the chain into an ordered list of narrators by splitting on the classical
transmission terms (حدثنا، أخبرنا، عن، سمعت…), then flag features that matter to
hadith critics: the transmission mode of each link (سماع vs عنعنة), تحويل (ح) when
multiple chains merge, and whether the chain reaches the Prophet ﷺ.

This is a *structural* read, not an authenticity verdict: grading the narrators
themselves needs a rijal (narrator-biography) database — see the note in the
output. That database is the cat-26 corpus, a planned ingestion step.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from app.parsing.normalize import normalize_for_search, strip_diacritics

# Transmission terms → mode. Keys are in the folded form of normalize_for_search.
_VIA: dict[str, str] = {
    "حدثنا": "سماع", "حدثني": "سماع", "حدثناه": "سماع", "ثنا": "سماع", "نا": "سماع",
    "اخبرنا": "سماع", "اخبرني": "سماع", "اخبرناه": "سماع", "انبانا": "سماع",
    "سمعت": "سماع", "سمعنا": "سماع", "سمع": "سماع", "سمعه": "سماع",
    "عن": "عنعنة", "عنه": "عنعنة",
}
# Connective words that are not narrator names.
_SKIP = {"قال", "قالا", "قالوا", "يعني", "قالت", "ح"}
_TOKEN = re.compile(r"[^\s،,.:؛()«»\"']+")


@dataclass(slots=True)
class Narrator:
    name: str
    via: str  # سماع | عنعنة | — (chain head)


@dataclass(slots=True)
class IsnadAnalysis:
    narrators: list[dict]
    length: int
    modes: dict[str, int]
    has_tahwil: bool          # ح — more than one route
    has_anana: bool           # عن — possible tadlīs, needs samāʿ confirmed
    reaches_prophet: bool
    notes: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def analyze_isnad(text: str) -> IsnadAnalysis:
    raw = strip_diacritics(text or "")
    narrators: list[Narrator] = []
    via: str | None = None
    buf: list[str] = []
    has_tahwil = False

    def flush() -> None:
        name = " ".join(buf).strip(" -،")
        if name:
            narrators.append(Narrator(name=name, via=via or "—"))

    for token in _TOKEN.findall(raw):
        folded = normalize_for_search(token)
        if token == "ح" or folded == "ح":
            has_tahwil = True  # تحويل: a standalone ح marks a route switch
            continue
        # accept a leading و (وحدثنا، وعن، وأخبرنا …)
        conn = folded if folded in _VIA else (
            folded[1:] if folded[:1] == "و" and folded[1:] in _VIA else None
        )
        if conn:
            flush()
            via, buf = _VIA[conn], []
            continue
        if folded in _SKIP:
            continue
        buf.append(token)
    flush()

    modes: dict[str, int] = {}
    for narrator in narrators:
        if narrator.via in ("سماع", "عنعنة"):
            modes[narrator.via] = modes.get(narrator.via, 0) + 1
    has_anana = modes.get("عنعنة", 0) > 0
    reaches_prophet = ("النبي" in raw) or ("رسول الله" in raw) or ("رسول اللـه" in raw)

    notes: list[str] = []
    if has_tahwil:
        notes.append("فيه تحويل (ح): أكثر من طريق في الإسناد.")
    if has_anana:
        notes.append("في الإسناد عنعنة؛ يُتحقَّق من ثبوت السماع (احتمال التدليس).")
    if len(narrators) < 3:
        notes.append("السند قصير؛ يُنظر في اتصاله.")
    notes.append("تقويم عدالة الرواة وضبطهم يتطلّب قاعدة بيانات الرجال (غير مُفعَّلة بعد).")

    return IsnadAnalysis(
        narrators=[asdict(n) for n in narrators],
        length=len(narrators),
        modes=modes,
        has_tahwil=has_tahwil,
        has_anana=has_anana,
        reaches_prophet=reaches_prophet,
        notes=notes,
    )
