"""Rutas, constantes y presets del editor.

Todo el dominio trabaja con `pathlib.Path`. El servidor HTTP sigue usando
`os.path` en la capa antigua, pero los módulos nuevos no dependen de ella.

La configuración del LLM se lee del entorno (o de un `.env` local) en el
servidor. La clave de API nunca se expone al frontend.
"""

from __future__ import annotations

import os

from manim_studio import PAQUETE_DIR, ROOT

# `BASE_DIR` se conserva como alias para los módulos heredados del servidor.
BASE_DIR = ROOT
WEB_DIR = PAQUETE_DIR / "web"

VAR_DIR = ROOT / "var"
MEDIA_DIR = VAR_DIR / "media"
EDITOR_MEDIA_DIR = MEDIA_DIR / "editor"
AUDIO_DIR = VAR_DIR / "audios"
DATA_DIR = VAR_DIR / "data"
PROJECTS_DIR = VAR_DIR / "proyectos"
DB_PATH = DATA_DIR / "editor.db"
TOKEN_PATH = DATA_DIR / "session_token"

# Rutas heredadas: se conservan para/scripts antiguos, pero el estudio trabaja
# dentro de PROJECTS_DIR/<slug>/escenas/.
ESCENAS_DIR = ROOT / "escenas"
MAIN_PY_PATH = ESCENAS_DIR / "main.py"
PASOS_ALGEBRAICOS_PATH = ESCENAS_DIR / "pasos_algebraicos.txt"

PLANTILLAS_DIR = PAQUETE_DIR / "motor" / "plantillas"
DOCS_DIR = ROOT / "docs"
REFERENCIA_TECNICA_PATH = DOCS_DIR / "REFERENCIA_TECNICA.md"

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


def _load_dotenv() -> None:
    """Carga `.env` sin sobrescribir variables ya definidas en el entorno."""

    path = ROOT / ".env"
    if not path.is_file():
        return
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv()


def _env_number(name: str, default: float, *, integer: bool = False) -> float | int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return int(default) if integer else float(default)
    try:
        value = int(raw) if integer else float(raw)
    except ValueError:
        return int(default) if integer else float(default)
    return max(1, value) if integer else max(1.0, value)


# OpenAI-compatible: sirve para OpenAI, DeepSeek, OpenRouter y Ollama.
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "mock").strip().lower()
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1").strip().rstrip("/")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
LLM_API_KEY = os.environ.get("LLM_API_KEY", "").strip()
LLM_TIMEOUT = float(_env_number("LLM_TIMEOUT", 45.0))
LLM_MAX_TOKENS = int(_env_number("LLM_MAX_TOKENS", 1200, integer=True))


def ensure_directories() -> None:
    for directory in (EDITOR_MEDIA_DIR, AUDIO_DIR, DATA_DIR, PROJECTS_DIR):
        directory.mkdir(parents=True, exist_ok=True)
