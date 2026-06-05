"""Video templates: different structures + color themes for the script.

Each template turns a topic into a list of `Scene`s with its own pacing,
scene kinds and color palette. Selecting a template changes the *structure*
of the video (e.g. quiz = question/answer pairs, top5 = countdown), while the
visual motion/animation is controlled separately at render time.

Add a new template by writing a `build_*` function and registering it in
`TEMPLATES`.
"""

from __future__ import annotations

import random
from typing import Callable, Dict, List

from .script_gen import Scene, Script, _estimate_seconds, generate_script

# --- color themes: list of (top, bottom, accent) RGB triples ----------------
_THEMES: Dict[str, List[tuple]] = {
    "sunset":  [((255, 94, 98), (255, 195, 113), (20, 20, 30)),
                ((247, 151, 30), (255, 81, 47), (20, 20, 30))],
    "ocean":   [((33, 147, 176), (109, 213, 237), (10, 30, 40)),
                ((0, 91, 154), (0, 180, 219), (255, 255, 255))],
    "neon":    [((131, 58, 180), (253, 29, 29), (255, 255, 255)),
                ((34, 0, 80), (180, 0, 255), (255, 255, 255))],
    "gold":    [((20, 20, 30), (60, 50, 20), (255, 200, 60)),
                ((40, 30, 10), (90, 70, 20), (255, 215, 90))],
}


def _cycle(theme: str, i: int) -> tuple:
    pal = _THEMES[theme]
    return pal[i % len(pal)]


def _finalize(scenes: List[Scene]) -> None:
    for i, s in enumerate(scenes):
        s.index = i
        if s.seconds <= 0:
            s.seconds = _estimate_seconds(s.text)


def _hashtags(topic: str, *extra: str) -> List[str]:
    base = ["#" + "".join(w.capitalize() for w in topic.split()[:3])]
    return base + list(extra) + ["#perte", "#fyp", "#viral"]


# --- classic: hook -> points -> cta ----------------------------------------

def build_classic(topic: str, num_points: int, rng: random.Random) -> Script:
    script = generate_script(topic, num_points=num_points, seed=rng.randint(0, 1_000_000))
    for i, s in enumerate(script.scenes):
        s.palette = _cycle("sunset", i)
    script.template = "classic"
    return script


# --- quiz: intro -> (question, answer) pairs -> outro ----------------------

_QUIZ_Q = [
    "Sai davvero questo su {topic}?",
    "Domanda: cosa succede con {topic}?",
    "Indovina: qual e' la verita' su {topic}?",
    "Test: conosci questo lato di {topic}?",
]
_QUIZ_A = [
    "La risposta e' piu' semplice di quanto pensi: parti dalle basi.",
    "Esatto: la maggior parte delle persone sbaglia proprio qui.",
    "La verita': bastano pochi giorni per vedere la differenza.",
    "Sorpresa: e' l'opposto di quello che credevi.",
]


def build_quiz(topic: str, num_points: int, rng: random.Random) -> Script:
    topic = topic.strip().rstrip(".")
    scenes = [Scene(0, "intro", f"Quiz lampo su {topic}. Quanti ne indovini?",
                    overlay="QUIZ", palette=_cycle("ocean", 0))]
    qs = rng.sample(_QUIZ_Q, k=min(num_points, len(_QUIZ_Q)))
    ans = rng.sample(_QUIZ_A, k=min(num_points, len(_QUIZ_A)))
    for i in range(len(qs)):
        scenes.append(Scene(0, "question", qs[i].format(topic=topic),
                            overlay=f"D{i+1}", palette=_cycle("ocean", 1)))
        scenes.append(Scene(0, "answer", ans[i],
                            overlay="RISPOSTA", palette=_cycle("gold", i)))
    scenes.append(Scene(0, "outro", f"Quanti ne hai indovinati su {topic}? "
                        f"Scrivilo e seguimi!", overlay="SEGUIMI",
                        palette=_cycle("neon", 0)))
    _finalize(scenes)
    return Script(topic=topic, title=f"Quiz: {topic}", template="quiz",
                  hashtags=_hashtags(topic, "#quiz", "#indovina"), scenes=scenes)


# --- top5: intro -> countdown ranks -> cta ---------------------------------

_RANK_LINES = [
    "perche' fa davvero la differenza ogni giorno.",
    "e quasi nessuno lo sfrutta come dovrebbe.",
    "ed e' il preferito di chi ottiene risultati.",
    "che cambia tutto se lo applichi subito.",
    "il segreto che gli esperti tengono per se'.",
]


def build_top5(topic: str, num_points: int, rng: random.Random) -> Script:
    topic = topic.strip().rstrip(".")
    n = max(2, min(num_points, 5))
    scenes = [Scene(0, "intro", f"I {n} migliori trucchi su {topic}. "
                    f"Il numero 1 ti sorprendera'.",
                    overlay=f"TOP {n}", palette=_cycle("neon", 1))]
    lines = rng.sample(_RANK_LINES, k=min(n, len(_RANK_LINES)))
    for rank in range(n, 0, -1):
        line = lines[(n - rank) % len(lines)]
        scenes.append(Scene(0, "rank",
                            f"Numero {rank}: un consiglio su {topic} {line}",
                            overlay=f"#{rank}", palette=_cycle("sunset", rank)))
    scenes.append(Scene(0, "cta", f"Quale useresti per primo? "
                        f"Salva il video e seguimi per altri su {topic}.",
                        overlay="SALVA", palette=_cycle("ocean", 0)))
    _finalize(scenes)
    return Script(topic=topic, title=f"Top {n}: {topic}", template="top5",
                  hashtags=_hashtags(topic, f"#top{n}", "#classifica"), scenes=scenes)


# --- storytelling: hook -> setup -> conflict -> resolution -> moral ---------

def build_story(topic: str, num_points: int, rng: random.Random) -> Script:
    topic = topic.strip().rstrip(".")
    beats = [
        ("hook", f"Ti racconto una storia su {topic} che cambia tutto.", "STORIA"),
        ("beat", f"All'inizio con {topic} sembrava tutto semplice.", "1"),
        ("beat", f"Poi e' arrivato il problema che nessuno si aspettava.", "2"),
        ("beat", f"La svolta e' stata capire una cosa su {topic}.", "3"),
        ("beat", f"Da quel momento e' cambiato tutto, in meglio.", "4"),
        ("cta", f"La morale? Non mollare con {topic}. Seguimi per la parte 2.", "SEGUIMI"),
    ]
    themes = ["gold", "ocean", "neon", "sunset"]
    scenes = []
    for i, (kind, text, ov) in enumerate(beats):
        scenes.append(Scene(0, kind, text, overlay=ov,
                            palette=_cycle(themes[i % len(themes)], i)))
    _finalize(scenes)
    return Script(topic=topic, title=f"La storia di {topic}", template="storytelling",
                  hashtags=_hashtags(topic, "#storytime", "#storia"), scenes=scenes)


TEMPLATES: Dict[str, Callable[[str, int, random.Random], Script]] = {
    "classic": build_classic,
    "quiz": build_quiz,
    "top5": build_top5,
    "storytelling": build_story,
}


def build_script(topic: str, template: str = "classic", num_points: int = 3,
                 seed: int | None = None) -> Script:
    if template not in TEMPLATES:
        raise ValueError(f"Template sconosciuto: {template}. "
                         f"Disponibili: {', '.join(TEMPLATES)}")
    rng = random.Random(seed)
    return TEMPLATES[template](topic, num_points, rng)
