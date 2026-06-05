"""Text-to-speech: a line of text becomes a WAV file.

Two fully-offline backends, selected automatically (best first):

  1. Piper  - neural TTS, very natural voice (preferred)
  2. espeak-ng - lightweight robotic fallback

Override with env vars:
  TTS_ENGINE = piper | espeak | auto   (default: auto)
  PIPER_MODEL = path to a .onnx voice  (default: models/piper/<lang voice>)

The public `synthesize` / `available` / `wav_duration` API is unchanged, so the
rest of the pipeline does not care which engine is used.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import wave
from pathlib import Path

ESPEAK = shutil.which("espeak-ng") or shutil.which("espeak")

# Known Piper voices per language (first = default). Download what you need with
# scripts/download_voices.py; only downloaded voices are offered at runtime.
PIPER_VOICES = {
    "it": ["it_IT-paola-medium", "it_IT-riccardo-x_low"],
    "en": ["en_US-amy-medium", "en_US-ryan-high", "en_GB-alan-medium"],
    "es": ["es_ES-davefx-medium", "es_MX-claude-high"],
    "ar": ["ar_JO-kareem-medium", "ar_JO-kareem-low"],
    "fr": ["fr_FR-siwis-medium"],
    "de": ["de_DE-thorsten-medium"],
    "pt": ["pt_BR-faber-medium"],
}
_PIPER_DEFAULT_VOICE = {lang: voices[0] for lang, voices in PIPER_VOICES.items()}
PIPER_DATA_DIR = Path(os.getenv("PIPER_DATA_DIR", "models/piper"))


class TTSUnavailable(RuntimeError):
    pass


def _voice_path(voice: str) -> Path:
    return PIPER_DATA_DIR / f"{voice}.onnx"


def list_voices(lang: str) -> list[str]:
    """Piper voices for `lang` that are actually downloaded."""
    return [v for v in PIPER_VOICES.get(lang, []) if _voice_path(v).exists()]


def all_voices() -> dict[str, list[str]]:
    """Downloaded voices grouped by language (for the API/UI selector)."""
    return {lang: v for lang in PIPER_VOICES if (v := list_voices(lang))}


def _resolve_voice(lang: str, voice: str | None) -> str | None:
    """Pick the Piper voice to use: explicit > env > first downloaded."""
    if voice and _voice_path(voice).exists():
        return voice
    env = os.getenv("PIPER_MODEL")
    if env and Path(env).exists():
        return env
    downloaded = list_voices(lang)
    return downloaded[0] if downloaded else None


def _piper_model_for(lang: str, voice: str | None = None) -> Path | None:
    chosen = _resolve_voice(lang, voice)
    if not chosen:
        return None
    # `chosen` may be an absolute path (PIPER_MODEL) or a known voice id
    p = Path(chosen)
    return p if p.suffix == ".onnx" and p.exists() else _voice_path(chosen)


def _piper_importable() -> bool:
    try:
        import piper  # noqa: F401
        return True
    except Exception:
        return False


def engine(lang: str = "it", voice: str | None = None) -> str:
    """Resolve which backend will actually be used for `lang`/`voice`."""
    choice = os.getenv("TTS_ENGINE", "auto").lower()
    model = _piper_model_for(lang, voice)
    piper_ok = _piper_importable() and model is not None and model.exists()
    if choice == "piper":
        return "piper" if piper_ok else "none"
    if choice == "espeak":
        return "espeak" if ESPEAK else "none"
    # auto: prefer piper, then espeak
    if piper_ok:
        return "piper"
    if ESPEAK:
        return "espeak"
    return "none"


def available(lang: str = "it", voice: str | None = None) -> bool:
    return engine(lang, voice) != "none"


def _synthesize_piper(text: str, out_path: Path, lang: str,
                      voice: str | None) -> Path:
    model = _piper_model_for(lang, voice)
    cmd = ["python3", "-m", "piper", "-m", str(model), "-f", str(out_path)]
    subprocess.run(cmd, input=text.encode("utf-8"), check=True, capture_output=True)
    return out_path


def _synthesize_espeak(text: str, out_path: Path, lang: str,
                       words_per_minute: int, pitch: int) -> Path:
    if not ESPEAK:
        raise TTSUnavailable("espeak-ng/espeak non trovato.")
    cmd = [ESPEAK, "-v", lang, "-s", str(words_per_minute), "-p", str(pitch),
           "-w", str(out_path), text]
    subprocess.run(cmd, check=True, capture_output=True)
    return out_path


def synthesize(text: str, out_path: Path, lang: str = "it",
               voice: str | None = None,
               words_per_minute: int = 165, pitch: int = 45) -> Path:
    """Render `text` to a WAV using the best available offline engine."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    eng = engine(lang, voice)
    if eng == "piper":
        return _synthesize_piper(text, out_path, lang, voice)
    if eng == "espeak":
        return _synthesize_espeak(text, out_path, lang, words_per_minute, pitch)
    raise TTSUnavailable(
        "Nessun motore TTS disponibile. Installa piper-tts + una voce, "
        "oppure: apt-get install espeak-ng")


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / float(w.getframerate())
