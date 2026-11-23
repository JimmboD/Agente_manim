"""Proyectos físicos del estudio y ajustes persistentes del servidor.

Cada proyecto vive en ``var/proyectos/<slug>/`` y contiene su propia carpeta
``escenas/``. Las plantillas de usuario y los audios siguen siendo globales.

Este módulo no depende del servidor HTTP para poder usarse desde tests y desde
el workspace sin importar ciclos.
"""

from __future__ import annotations

import json
import re
import shutil
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from manim_studio.editor.config import (
    DATA_DIR,
    ESCENAS_DIR,
    PROJECTS_DIR,
)

META_NAME = "proyecto.json"
ACTIVE_FILE = DATA_DIR / "active_project"
SETTINGS_FILE = DATA_DIR / "settings.json"
DEFAULT_TITLE = "Mi proyecto"
DEFAULT_SLUG = "mi_proyecto"
SLUG_RE = re.compile(r"^[A-Za-z0-9_-]{1,80}$")

MAIN_SCAFFOLD = '''# -*- coding: utf-8 -*-
"""Escena principal de {title}."""

# Escribe aquí tu animación. El botón «Ejecutar» usa este archivo.
if __name__ == "__main__":
    pass
'''


class ProjectError(ValueError):
    """Error de validación de proyectos o ajustes."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def slugify(title: str) -> str:
    text = unicodedata.normalize("NFKD", str(title or "")).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^A-Za-z0-9_-]+", "_", text).strip("_")
    return text[:80] or DEFAULT_SLUG


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path, default: dict) -> dict:
    if not path.is_file():
        return dict(default)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else dict(default)
    except (OSError, json.JSONDecodeError):
        return dict(default)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def ensure_directories() -> None:
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _validate_slug(slug: str) -> str:
    clean = str(slug or "").strip()
    if not SLUG_RE.fullmatch(clean):
        raise ProjectError(400, "Identificador de proyecto no válido.")
    return clean


def project_dir(slug: str) -> Path:
    return PROJECTS_DIR / _validate_slug(slug)


def scenes_dir(slug: str) -> Path:
    return project_dir(slug) / "escenas"


def main_py_path(slug: str) -> Path:
    return scenes_dir(slug) / "main.py"


def pasos_path(slug: str) -> Path:
    return scenes_dir(slug) / "pasos_algebraicos.txt"


def _meta_path(slug: str) -> Path:
    return project_dir(slug) / META_NAME


def _project_from_dir(path: Path) -> dict:
    meta = _read_json(path / META_NAME, {})
    slug = str(meta.get("slug") or path.name)
    title = str(meta.get("title") or slug.replace("_", " ").title())
    scenes = path / "escenas"
    return {
        "slug": slug,
        "title": title,
        "path": str(path),
        "scenesPath": str(scenes),
        "created": str(meta.get("created") or ""),
        "modified": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
        "hasMain": (scenes / "main.py").is_file(),
    }


def list_projects() -> list[dict]:
    ensure_directories()
    items = []
    for path in PROJECTS_DIR.iterdir():
        if path.is_dir() and SLUG_RE.fullmatch(path.name):
            items.append(_project_from_dir(path))
    items.sort(key=lambda item: (item["title"].lower(), item["slug"]))
    return items


def active_slug() -> str:
    ensure_directories()
    stored = ACTIVE_FILE.read_text(encoding="utf-8").strip() if ACTIVE_FILE.is_file() else ""
    projects = list_projects()
    slugs = {item["slug"] for item in projects}
    if stored in slugs:
        return stored
    return projects[0]["slug"] if projects else ""


def set_active(slug: str) -> dict:
    clean = _validate_slug(slug)
    if not project_dir(clean).is_dir():
        raise ProjectError(404, "El proyecto no existe.")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ACTIVE_FILE.write_text(clean, encoding="utf-8")
    return {"slug": clean, "active": True}


def create_project(title: str, *, copy_from: Path | None = None) -> dict:
    clean_title = str(title or "").strip()
    if not clean_title:
        raise ProjectError(400, "Escribe un título para el proyecto.")
    if len(clean_title) > 120:
        raise ProjectError(400, "El título es demasiado largo.")

    ensure_directories()
    existing = {item["slug"] for item in list_projects()}
    base = slugify(clean_title)
    slug = base
    index = 2
    while slug in existing:
        suffix = f"_{index}"
        slug = f"{base[:80 - len(suffix)]}{suffix}"
        index += 1

    base_dir = project_dir(slug)
    scenes = scenes_dir(slug)
    scenes.mkdir(parents=True, exist_ok=True)
    if copy_from is not None and copy_from.is_dir():
        shutil.copytree(
            copy_from,
            scenes,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("__pycache__"),
        )
    if not (scenes / "main.py").exists():
        (scenes / "main.py").write_text(
            MAIN_SCAFFOLD.format(title=clean_title), encoding="utf-8"
        )
    _write_json(
        _meta_path(slug),
        {"slug": slug, "title": clean_title, "created": _now()},
    )
    set_active(slug)
    return _project_from_dir(base_dir)


def ensure_initial_project() -> dict:
    """Crea el proyecto inicial y migra el contenido heredado de ``escenas/``."""

    ensure_directories()
    projects = list_projects()
    if not projects:
        return create_project(DEFAULT_TITLE, copy_from=ESCENAS_DIR)
    if not active_slug():
        set_active(projects[0]["slug"])
    return next(item for item in projects if item["slug"] == active_slug())


def delete_project(slug: str) -> dict:
    clean = _validate_slug(slug)
    target = project_dir(clean)
    if not target.is_dir():
        raise ProjectError(404, "El proyecto no existe.")
    projects = list_projects()
    if len(projects) <= 1:
        raise ProjectError(400, "Debe quedar al menos un proyecto.")
    shutil.rmtree(target)
    if active_slug() == clean:
        remaining = [item["slug"] for item in projects if item["slug"] != clean]
        set_active(remaining[0])
    return {"deleted": clean, "active": active_slug()}


DEFAULT_SETTINGS = {"unlock_system_templates": False}


def get_settings() -> dict:
    data = _read_json(SETTINGS_FILE, DEFAULT_SETTINGS)
    return {
        "unlockSystemTemplates": bool(
            data.get("unlockSystemTemplates", data.get("unlock_system_templates", False))
        )
    }


def update_settings(patch: dict) -> dict:
    current = get_settings()
    if "unlockSystemTemplates" in patch:
        value = patch["unlockSystemTemplates"]
        if not isinstance(value, bool):
            raise ProjectError(400, "unlockSystemTemplates debe ser booleano.")
        current["unlockSystemTemplates"] = value
    _write_json(SETTINGS_FILE, current)
    return current
