"""Subtitle generation: build an SRT file from timed scenes."""

from __future__ import annotations

from pathlib import Path
from typing import List


def _ts(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_srt(lines: List[tuple[str, float]], out_path: Path) -> Path:
    """`lines` is a list of (text, duration_seconds)."""
    out, t = [], 0.0
    for i, (text, dur) in enumerate(lines, start=1):
        start, end = t, t + dur
        out.append(f"{i}\n{_ts(start)} --> {_ts(end)}\n{text}\n")
        t = end
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(out), encoding="utf-8")
    return out_path
