"""Video assembly with FFmpeg: frames + per-scene audio + burned subtitles -> mp4.

Each scene is a still frame shown for the exact duration of its narration audio.
Scenes are concatenated, the full narration is laid under the video, optional
background music is mixed in, and the .srt is burned on top.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

FFMPEG = shutil.which("ffmpeg")

WIDTH, HEIGHT, FPS = 1080, 1920, 30


class FFmpegUnavailable(RuntimeError):
    pass


def available() -> bool:
    return FFMPEG is not None


@dataclass
class Clip:
    image: Path
    audio: Path
    duration: float


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, capture_output=True)


def _render_clip(clip: Clip, out: Path) -> None:
    """One still image + its audio -> a short mp4 of exact duration."""
    _run([
        FFMPEG, "-y",
        "-loop", "1", "-framerate", str(FPS), "-t", f"{clip.duration:.3f}", "-i", str(clip.image),
        "-i", str(clip.audio),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        "-vf", f"scale={WIDTH}:{HEIGHT},setsar=1",
        "-shortest", "-t", f"{clip.duration:.3f}",
        str(out),
    ])


def assemble(clips: List[Clip], out_path: Path,
             subtitles: Optional[Path] = None,
             music: Optional[Path] = None,
             music_volume: float = 0.12) -> Path:
    if not available():
        raise FFmpegUnavailable("ffmpeg not found. Install with: apt-get install ffmpeg")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        parts: List[Path] = []
        for i, clip in enumerate(clips):
            part = tmp / f"part_{i:02d}.mp4"
            _render_clip(clip, part)
            parts.append(part)

        # concat demuxer
        concat_file = tmp / "concat.txt"
        concat_file.write_text(
            "".join(f"file '{p}'\n" for p in parts), encoding="utf-8")

        joined = tmp / "joined.mp4"
        _run([
            FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file),
            "-c", "copy", str(joined),
        ])

        current = joined

        # optional background music mixed under the narration
        if music and Path(music).exists():
            mixed = tmp / "mixed.mp4"
            _run([
                FFMPEG, "-y", "-i", str(current), "-stream_loop", "-1", "-i", str(music),
                "-filter_complex",
                f"[1:a]volume={music_volume}[m];[0:a][m]amix=inputs=2:duration=first:dropout_transition=2[a]",
                "-map", "0:v", "-map", "[a]",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                str(mixed),
            ])
            current = mixed

        # optional burned-in subtitles
        if subtitles and Path(subtitles).exists():
            subbed = tmp / "subbed.mp4"
            style = ("FontName=DejaVu Sans,Fontsize=14,PrimaryColour=&H00FFFFFF,"
                     "OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=1,"
                     "Alignment=2,MarginV=120")
            _run([
                FFMPEG, "-y", "-i", str(current),
                "-vf", f"subtitles={subtitles}:force_style='{style}'",
                "-c:a", "copy", str(subbed),
            ])
            current = subbed

        shutil.copy(current, out_path)

    return out_path
