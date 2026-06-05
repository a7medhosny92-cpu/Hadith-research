"""Command-line entry point: render a full video from a topic.

    python3 cli.py "la produttività" --points 3 --lang it --out output/cli
"""

from __future__ import annotations

import argparse
from pathlib import Path

from app.pipeline.orchestrator import create_video


def main() -> None:
    ap = argparse.ArgumentParser(description="Genera un video virale verticale da un argomento.")
    ap.add_argument("topic", nargs="?", help="Argomento del video")
    ap.add_argument("--points", type=int, default=3, help="Numero di punti chiave (1-5)")
    ap.add_argument("--lang", default="it", help="Lingua (it, en, es, ar, ...)")
    ap.add_argument("--voice", default=None,
                    help="Voce Piper specifica (vedi --list-voices)")
    ap.add_argument("--list-voices", action="store_true",
                    help="Elenca le voci scaricate per lingua ed esce")
    ap.add_argument("--seed", type=int, default=None, help="Seed riproducibile")
    ap.add_argument("--style", choices=["slide", "ai"], default="slide",
                    help="Stile visivo: slide (gradienti) o ai (Stable Diffusion)")
    ap.add_argument("--template", choices=["classic", "quiz", "top5", "storytelling"],
                    default="classic", help="Template/struttura del video")
    ap.add_argument("--no-animate", dest="animate", action="store_false",
                    help="Disattiva movimento e testo animato (frame statici)")
    ap.add_argument("--broll", action="store_true",
                    help="Usa clip b-roll da assets/broll come sfondo")
    ap.add_argument("--transition", choices=["crossfade", "cut"], default="crossfade",
                    help="Transizione tra le scene")
    ap.add_argument("--music", default=None, help="File audio di sottofondo (opzionale)")
    ap.add_argument("--out", default="output/cli", help="Cartella di output")
    args = ap.parse_args()

    if args.list_voices:
        from app.pipeline.tts import all_voices, PIPER_VOICES
        downloaded = all_voices()
        print("  Voci scaricate per lingua:")
        for lang, voices in PIPER_VOICES.items():
            have = downloaded.get(lang, [])
            for v in voices:
                mark = "✓" if v in have else " "
                print(f"   [{mark}] {lang}: {v}")
        return

    if not args.topic:
        ap.error("argomento mancante (oppure usa --list-voices)")

    def progress(stage: str, pct: float) -> None:
        print(f"  [{pct*100:5.1f}%] {stage}")

    music = Path(args.music) if args.music else None
    result = create_video(
        topic=args.topic, workdir=Path(args.out), num_points=args.points,
        lang=args.lang, voice=args.voice, music=music, seed=args.seed,
        style=args.style, template=args.template, animate=args.animate,
        use_broll=args.broll, transition=args.transition, progress=progress,
    )

    print("\n  TITOLO :", result.script.title)
    print("  HASHTAG:", " ".join(result.script.hashtags))
    if result.video:
        print("  VIDEO  :", result.video)
    print("  FRAME  :", len(result.frames), "->", result.workdir)
    for w in result.warnings:
        print("  ! ", w)


if __name__ == "__main__":
    main()
