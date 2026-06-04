"""Text-to-speech: a line of text becomes a WAV file.

Default backend is espeak-ng (fully offline, no API). The backend is selected
behind a single `synthesize` function so a higher quality local engine such as
Piper can be swapped in later without changing the pipeline.
"""

from __future__ import annotations

import shutil
import subprocess
import wave
from pathlib import Path

ESPEAK = shutil.which("espeak-ng") or shutil.which("espeak")


class TTSUnavailable(RuntimeError):
    pass


def available() -> bool:
    return ESPEAK is not None


def synthesize(text: str, out_path: Path, lang: str = "it",
               words_per_minute: int = 165, pitch: int = 45) -> Path:
    """Render `text` to a 22.05kHz mono WAV using espeak-ng."""
    if not available():
        raise TTSUnavailable(
            "espeak-ng/espeak not found. Install with: apt-get install espeak-ng")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ESPEAK, "-v", lang, "-s", str(words_per_minute), "-p", str(pitch),
        "-w", str(out_path), text,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return out_path


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / float(w.getframerate())
