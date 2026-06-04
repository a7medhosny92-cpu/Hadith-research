"""Offline demo: topic -> script -> frames -> subtitles -> storyboard.

Produces everything except the final muxed .mp4 (which needs FFmpeg + a TTS
engine). Run:  python3 demo.py "la produttivita"
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from app.pipeline.script_gen import generate_script
from app.pipeline.visuals import render_scene, storyboard
from app.pipeline.subtitles import build_srt

OUT = Path("output/demo")


def main(topic: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    script = generate_script(topic, num_points=3, seed=7)

    print(f"\n  TITOLO : {script.title}")
    print(f"  HASHTAG: {' '.join(script.hashtags)}")
    print(f"  DURATA : ~{sum(s.seconds for s in script.scenes):.1f}s\n")

    frames = []
    for s in script.scenes:
        print(f"  [{s.kind:5}] {s.seconds:4.1f}s  {s.text}")
        frame = render_scene(
            kind=s.kind, text=s.text, overlay=s.overlay,
            out_path=OUT / f"frame_{s.index:02d}.png",
            index=s.index, total=len(script.scenes),
        )
        frames.append(frame)

    sheet = storyboard(frames, OUT / "storyboard.png")
    srt = build_srt([(s.text, s.seconds) for s in script.scenes], OUT / "captions.srt")
    (OUT / "script.json").write_text(
        json.dumps(script.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n  -> {len(frames)} frame in {OUT}/")
    print(f"  -> storyboard: {sheet}")
    print(f"  -> sottotitoli: {srt}")
    print(f"  -> script.json: {OUT/'script.json'}\n")


if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else "la produttivita"
    main(topic)
