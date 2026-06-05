"""Download Piper voices for one or more languages.

    python3 scripts/download_voices.py it en es ar      # default voice per lang
    python3 scripts/download_voices.py --all it en      # every known voice
    python3 scripts/download_voices.py                  # the default set

Voices are saved under PIPER_DATA_DIR (default: models/piper) and picked up
automatically by the TTS engine / voice selector.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.pipeline.tts import PIPER_VOICES, _PIPER_DEFAULT_VOICE, PIPER_DATA_DIR

DEFAULT_LANGS = ["it", "en", "es", "ar"]


def main(argv: list[str]) -> None:
    want_all = "--all" in argv
    langs = [a for a in argv if not a.startswith("-")] or DEFAULT_LANGS
    PIPER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    for lang in langs:
        voices = PIPER_VOICES.get(lang, []) if want_all \
            else [_PIPER_DEFAULT_VOICE.get(lang)]
        for voice in filter(None, voices):
            print(f"  scarico {lang} -> {voice} ...")
            subprocess.run(
                [sys.executable, "-m", "piper.download_voices", voice,
                 "--data-dir", str(PIPER_DATA_DIR)],
                check=True)
    print(f"  fatto. Voci in {PIPER_DATA_DIR}/")


if __name__ == "__main__":
    main(sys.argv[1:])
