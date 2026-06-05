"""Script generation: a topic/prompt becomes a structured viral video script.

The default generator is fully offline and template-based so the pipeline works
with zero paid APIs. It is intentionally written behind a small interface so a
local LLM (e.g. Ollama) can be plugged in later without touching the rest of
the pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List
import random
import textwrap


@dataclass
class Scene:
    """A single beat of the video."""

    index: int
    kind: str              # hook | point | cta | question | answer | rank | intro | outro | beat
    text: str              # the on-screen / spoken line
    overlay: str = ""      # short caption burned over the visual
    seconds: float = 0.0   # estimated duration, filled in later
    palette: tuple | None = None  # optional (top, bottom, accent) RGB override


@dataclass
class Script:
    topic: str
    title: str
    hashtags: List[str]
    scenes: List[Scene] = field(default_factory=list)
    template: str = "classic"

    @property
    def narration(self) -> str:
        return " ".join(s.text for s in self.scenes)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["narration"] = self.narration
        return d


# --- offline template-based generator -------------------------------------

_HOOKS = [
    "Nessuno ti ha mai spiegato questo su {topic}.",
    "Sto per cambiarti il modo di vedere {topic}.",
    "3 cose su {topic} che ti faranno dire 'wow'.",
    "Smetti di sbagliare con {topic}. Guarda qui.",
    "Il segreto su {topic} che gli esperti non dicono.",
]

_CTAS = [
    "Salva questo video prima che sparisca. Seguimi per altro su {topic}.",
    "Quale ti ha sorpreso di piu'? Scrivilo nei commenti.",
    "Condividilo con chi deve assolutamente sapere questo su {topic}.",
    "Seguimi: ogni giorno un nuovo trucco su {topic}.",
]

_POINT_TEMPLATES = [
    "Punto {n}: {topic} funziona meglio quando parti dalle basi.",
    "Punto {n}: la maggior parte delle persone ignora questo dettaglio su {topic}.",
    "Punto {n}: un piccolo cambiamento qui fa una differenza enorme.",
    "Punto {n}: ecco l'errore numero uno da evitare con {topic}.",
    "Punto {n}: prova questo per 7 giorni e vedrai i risultati.",
]


def _estimate_seconds(text: str) -> float:
    # ~2.6 words/second is a natural, punchy social-video pace.
    words = max(1, len(text.split()))
    return round(max(1.6, words / 2.6), 2)


def generate_script(topic: str, num_points: int = 3, seed: int | None = None) -> Script:
    """Build a hook -> points -> CTA script from a topic, fully offline."""
    rng = random.Random(seed)
    topic = topic.strip().rstrip(".")

    hook = rng.choice(_HOOKS).format(topic=topic)
    cta = rng.choice(_CTAS).format(topic=topic)
    point_pool = rng.sample(_POINT_TEMPLATES, k=min(num_points, len(_POINT_TEMPLATES)))

    scenes: List[Scene] = []
    scenes.append(Scene(index=0, kind="hook", text=hook, overlay="ASPETTA..."))
    for i, tmpl in enumerate(point_pool, start=1):
        text = tmpl.format(n=i, topic=topic)
        scenes.append(Scene(index=i, kind="point", text=text, overlay=f"#{i}"))
    scenes.append(Scene(index=len(scenes), kind="cta", text=cta, overlay="SEGUIMI"))

    for s in scenes:
        s.seconds = _estimate_seconds(s.text)

    title = textwrap.shorten(f"{topic.capitalize()}: quello che devi sapere", width=60)
    hashtags = ["#" + "".join(w.capitalize() for w in topic.split()[:3]),
                "#viral", "#perte", "#imparacon", "#fyp"]

    return Script(topic=topic, title=title, hashtags=hashtags, scenes=scenes)
