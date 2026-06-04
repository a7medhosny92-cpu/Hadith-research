"""Runtime configuration via environment variables."""

from __future__ import annotations

import os
from pathlib import Path

OUTPUT_ROOT = Path(os.getenv("VIDEO_OUTPUT_ROOT", "output/jobs")).resolve()
MAX_WORKERS = int(os.getenv("VIDEO_MAX_WORKERS", "2"))
DEFAULT_LANG = os.getenv("VIDEO_DEFAULT_LANG", "it")
