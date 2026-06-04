"""Tests for the offline portions of the pipeline.

Stages that need external binaries (espeak-ng, ffmpeg) are skipped when those
binaries are absent, so the suite passes in any environment.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.pipeline.script_gen import generate_script
from app.pipeline.visuals import render_scene, storyboard, WIDTH, HEIGHT
from app.pipeline.subtitles import build_srt
from app.pipeline.orchestrator import create_video
from app.pipeline import tts, assembler


def test_script_structure_is_hook_points_cta():
    s = generate_script("la produttività", num_points=3, seed=1)
    kinds = [sc.kind for sc in s.scenes]
    assert kinds[0] == "hook"
    assert kinds[-1] == "cta"
    assert kinds.count("point") == 3
    assert all(sc.seconds > 0 for sc in s.scenes)
    assert s.title and s.hashtags


def test_script_is_reproducible_with_seed():
    a = generate_script("spazio", seed=42)
    b = generate_script("spazio", seed=42)
    assert a.narration == b.narration


def test_render_scene_produces_vertical_frame(tmp_path: Path):
    from PIL import Image

    out = render_scene("hook", "Testo di prova abbastanza lungo da andare a capo",
                       "ASPETTA", tmp_path / "f.png", index=0, total=3)
    assert out.exists()
    with Image.open(out) as im:
        assert im.size == (WIDTH, HEIGHT)


def test_storyboard_combines_frames(tmp_path: Path):
    frames = [render_scene("point", f"linea {i}", f"#{i}", tmp_path / f"f{i}.png",
                           index=i, total=3) for i in range(3)]
    sheet = storyboard(frames, tmp_path / "sheet.png")
    assert sheet.exists()


def test_build_srt_format(tmp_path: Path):
    srt = build_srt([("ciao", 2.0), ("mondo", 1.5)], tmp_path / "c.srt")
    text = srt.read_text(encoding="utf-8")
    assert "00:00:00,000 --> 00:00:02,000" in text
    assert "00:00:02,000 --> 00:00:03,500" in text


def test_pipeline_produces_artifacts(tmp_path: Path):
    result = create_video("test argomento", workdir=tmp_path, num_points=2, seed=3)
    assert len(result.frames) == len(result.script.scenes)
    assert result.storyboard.exists()
    assert result.subtitles.exists()
    assert (tmp_path / "script.json").exists()


@pytest.mark.skipif(not tts.available(), reason="espeak-ng non installato")
def test_tts_creates_audio(tmp_path: Path):
    wav = tts.synthesize("prova della sintesi vocale", tmp_path / "v.wav", lang="it")
    assert wav.exists()
    assert tts.wav_duration(wav) > 0


@pytest.mark.skipif(not (tts.available() and assembler.available()),
                    reason="ffmpeg/espeak-ng non installati")
def test_full_video_render(tmp_path: Path):
    result = create_video("video completo di prova", workdir=tmp_path,
                          num_points=2, seed=5)
    assert result.video is not None
    assert result.video.exists()
    assert result.video.stat().st_size > 0
