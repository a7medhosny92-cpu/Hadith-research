FROM python:3.11-slim

# System tools: FFmpeg (montaggio) + espeak-ng (fallback voce)
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg espeak-ng fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Voce neurale Piper (italiano). Commenta per immagini più leggere.
RUN python3 -m piper.download_voices it_IT-paola-medium --data-dir models/piper

COPY . .

ENV PIPER_DATA_DIR=/app/models/piper \
    VIDEO_OUTPUT_ROOT=/app/output/jobs

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
