"""B-roll background clips from a local library.

To stay fully offline and free of paid APIs, b-roll is sourced from a local
folder of video files (default: assets/broll, override with BROLL_DIR). Clips
are matched to a scene by filename keyword when possible, otherwise picked at
random. If the folder is empty, `pick` returns None and the pipeline falls back
to still frames with Ken Burns motion.

Drop your own royalty-free .mp4/.mov/.webm clips into assets/broll to enable it.
"""

from __future__ import annotations

import os
import random
import re
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

BROLL_DIR = Path(os.getenv("BROLL_DIR", "assets/broll"))
_EXTS = {".mp4", ".mov", ".webm", ".mkv", ".m4v"}


@lru_cache(maxsize=1)
def _library() -> tuple:
    if not BROLL_DIR.exists():
        return tuple()
    return tuple(sorted(p for p in BROLL_DIR.iterdir()
                        if p.suffix.lower() in _EXTS))


def available() -> bool:
    return len(_library()) > 0


def _keywords(text: str) -> List[str]:
    return [w for w in re.findall(r"[a-zA-Zàèéìòù]+", text.lower()) if len(w) > 3]


def pick(topic: str, scene_text: str, seed: Optional[int] = None) -> Optional[Path]:
    """Choose a b-roll clip for a scene, by keyword match then random."""
    lib = _library()
    if not lib:
        return None
    rng = random.Random(seed)
    keywords = set(_keywords(topic) + _keywords(scene_text))
    scored = []
    for clip in lib:
        name = clip.stem.lower()
        score = sum(1 for k in keywords if k in name)
        scored.append((score, clip))
    best = max(s for s, _ in scored)
    candidates = [c for s, c in scored if s == best]
    return rng.choice(candidates)
