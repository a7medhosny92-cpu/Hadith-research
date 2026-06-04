# Viral Video Backend

Pipeline **end-to-end e completamente offline** che trasforma un semplice
argomento in un **video verticale** (1080×1920) pronto per TikTok / Reels /
Shorts: script → voce → frame → sottotitoli → `.mp4`.

Nessuna API a pagamento: usa **FFmpeg** (montaggio), **espeak-ng** (voce TTS) e
**Pillow** (grafica). Ogni modulo AI è "pluggable": puoi collegare in seguito un
LLM locale (Ollama) per script più ricchi o Stable Diffusion per immagini
realistiche, senza riscrivere la pipeline.

## Cosa produce

Dato un argomento (es. *"la produttività"*) genera automaticamente:

- **Script** strutturato: Hook → N punti chiave → Call-to-action
- **Voce narrante** per ogni scena (TTS offline)
- **Frame verticali** 1080×1920 con badge, testo auto-dimensionato, dots di progresso
- **Sottotitoli** `.srt` sincronizzati con il parlato
- **Storyboard** (contact sheet) per l'anteprima rapida
- **Video finale** `video.mp4` (H.264 + AAC) con voce, sottotitoli a fuoco e
  musica opzionale
- **`script.json`** con titolo e hashtag ottimizzati

## Requisiti

```bash
# strumenti di sistema
apt-get install -y ffmpeg espeak-ng

# dipendenze Python
pip install -r requirements.txt
```

> Senza `ffmpeg`/`espeak-ng` la pipeline funziona comunque e produce script,
> frame, storyboard e sottotitoli (salta solo voce e `.mp4`).

## Uso

### CLI

```bash
python3 cli.py "la produttività" --points 3 --lang it --seed 7 --out output/sample
# con musica di sottofondo opzionale:
python3 cli.py "il caffè" --music assets/musica.mp3
```

### API (FastAPI)

```bash
uvicorn app.main:app --reload
```

| Metodo | Endpoint | Descrizione |
|---|---|---|
| `GET`  | `/` | health + capacità (ffmpeg/tts disponibili) |
| `POST` | `/videos` | crea un job: `{"topic": "...", "num_points": 3, "lang": "it"}` |
| `GET`  | `/videos/{id}` | stato del job + link agli artefatti |
| `GET`  | `/videos/{id}/files/{name}` | scarica un artefatto (es. `video.mp4`) |

Esempio:

```bash
curl -X POST localhost:8000/videos -H 'content-type: application/json' \
     -d '{"topic":"la produttività","num_points":3,"lang":"it"}'
# -> {"id":"abc123...","state":"queued",...}
curl localhost:8000/videos/abc123
# quando state == "done": scarica il video
curl -OJ localhost:8000/videos/abc123/files/video.mp4
```

## Struttura

```
app/
├── main.py              # API FastAPI
├── jobs.py              # job store in background (thread pool)
├── models.py            # schemi Pydantic
├── config.py            # configurazione via env
└── pipeline/
    ├── script_gen.py    # argomento → script (hook/punti/cta)
    ├── tts.py           # testo → voce (espeak-ng)
    ├── visuals.py       # scena → frame 1080×1920 (Pillow)
    ├── subtitles.py     # scene → .srt
    ├── assembler.py     # frame + voce + sottotitoli → .mp4 (ffmpeg)
    └── orchestrator.py  # pipeline end-to-end
cli.py                   # entry point a riga di comando
demo.py                  # demo offline (senza ffmpeg/tts)
tests/                   # pytest (salta gli stage senza i binari)
```

## Test

```bash
python3 -m pytest -q
```

I test che richiedono `ffmpeg`/`espeak-ng` vengono saltati automaticamente se i
binari non sono presenti.

## Estensioni future

- **Script migliori**: backend LLM locale (Ollama) dietro `script_gen.py`
- **Immagini realistiche**: Stable Diffusion locale dietro `visuals.render_scene`
- **Voce premium**: Piper TTS dietro `tts.synthesize`
- **Persistenza job**: Celery/RQ + Redis al posto del thread pool
