#!/usr/bin/env bash
# Avvia il Tutor di Arabo Classico/Coranico con un comando solo.
#   ./run_tutor.sh            → http://localhost:8000
#   PORT=9000 ./run_tutor.sh  → porta personalizzata
set -e
cd "$(dirname "$0")"

PY="${PYTHON:-python3}"
PORT="${PORT:-8000}"

echo "→ Installo le dipendenze del tutor (fastapi, uvicorn, pydantic)…"
"$PY" -m pip install -q -r requirements-tutor.txt

echo "→ Avvio il tutor su http://localhost:${PORT}  (Ctrl+C per fermare)"
exec "$PY" -m uvicorn app.arabic.web:app --host 0.0.0.0 --port "$PORT"
