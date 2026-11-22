"""Seguridad local: contención de rutas, token de sesión y CORS.

El editor está pensado para ejecutarse en 127.0.0.1. Aun así, cualquier página
abierta en el navegador puede intentar hablar con localhost, así que las
peticiones mutantes exigen un token y un Origin permitido.
"""

from __future__ import annotations

import hmac
import secrets
from pathlib import Path
from urllib.parse import urlsplit


class UnsafePathError(ValueError):
    """La ruta solicitada intenta salir del directorio permitido."""


def safe_join(base: Path | str, relative: str) -> Path:
    """Resuelve `relative` dentro de `base` y falla si escapa.

    Acepta tanto separadores `/` como `\\` para cubrir peticiones de Windows.
    """

    base_path = Path(base).resolve()
    raw = (relative or "").replace("\\", "/").lstrip("/")
    target = (base_path / raw).resolve()

    if target != base_path and base_path not in target.parents:
        raise UnsafePathError(f"Ruta fuera de {base_path}: {relative!r}")
    return target


def ensure_token(path: Path | str) -> str:
    """Lee el token de sesión o lo crea con permisos de usuario."""

    token_path = Path(path)
    if token_path.is_file():
        token = token_path.read_text(encoding="utf-8").strip()
        if token:
            return token

    token = secrets.token_urlsafe(32)
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(token, encoding="utf-8")
    try:
        token_path.chmod(0o600)
    except OSError:
        # En Windows chmod es limitado; el archivo vive en una carpeta local.
        pass
    return token


def token_matches(expected: str, provided: str | None) -> bool:
    if not expected or not provided:
        return False
    return hmac.compare_digest(expected, provided)


def allowed_origins(port: int) -> set[str]:
    return {
        f"http://127.0.0.1:{port}",
        f"http://localhost:{port}",
        f"http://[::1]:{port}",
    }


def origin_is_allowed(origin: str | None, allowed: set[str]) -> bool:
    if not origin:
        return True
    return origin in allowed


def normalize_origin(value: str | None) -> str | None:
    """Extrae scheme://host:port de un Origin o Referer."""

    if not value:
        return None
    parts = urlsplit(value)
    if not parts.scheme or not parts.netloc:
        return None
    return f"{parts.scheme}://{parts.netloc}"
