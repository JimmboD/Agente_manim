"""Rutas, constantes y presets del editor.

Todo el dominio trabaja con `pathlib.Path`. El servidor HTTP sigue usando
`os.path` en la capa antigua, pero los módulos nuevos no dependen de ella.
"""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / "web"
MEDIA_DIR = BASE_DIR / "media"
EDITOR_MEDIA_DIR = MEDIA_DIR / "editor"
AUDIO_DIR = BASE_DIR / "audios"
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "editor.db"
TOKEN_PATH = DATA_DIR / "session_token"

HOST = "127.0.0.1"
PORT = int(os.environ.get("MANIM_STUDIO_PORT", "5000"))

# Relación de aspecto -> metadatos de layout.
# `aspect` es ancho/alto y se usa para el encuadre de la cámara.
FORMATS = {
    "16:9": {
        "label": "Horizontal 16:9",
        "aspect": 16 / 9,
        "pixel": (1920, 1080),
        "preview": (854, 480),
    },
    "9:16": {
        "label": "Vertical 9:16",
        "aspect": 9 / 16,
        "pixel": (1080, 1920),
        "preview": (480, 854),
    },
    "1:1": {
        "label": "Cuadrado 1:1",
        "aspect": 1.0,
        "pixel": (1080, 1080),
        "preview": (720, 720),
    },
}

QUALITIES = {
    "low_quality": {"label": "Previsualización (480p15)", "height": 480},
    "medium_quality": {"label": "Media (720p30)", "height": 720},
    "high_quality": {"label": "Alta (1080p60)", "height": 1080},
}

DEFAULT_FORMAT = "16:9"
DEFAULT_QUALITY = "low_quality"

# Límites de seguridad.
MAX_UPLOAD_BYTES = 50 * 1024 * 1024
ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac"}


def ensure_directories() -> None:
    for directory in (EDITOR_MEDIA_DIR, AUDIO_DIR, DATA_DIR):
        directory.mkdir(parents=True, exist_ok=True)
