"""Gestión segura del espacio de trabajo del estudio.

Expone un árbol de carpetas acotado al proyecto y operaciones de lectura,
escritura, creación, movimiento, borrado y subida. Todas las rutas se
resuelven con :func:`safe_join` contra una raíz explícita: ninguna petición
puede escapar de ``escenas/``, ``var/`` o del paquete de plantillas.
"""

from __future__ import annotations

import base64
import hashlib
import os
import re
import shutil
import unicodedata
from datetime import datetime, timezone
from urllib.parse import quote
from pathlib import Path, PurePosixPath

from manim_studio.editor import projects
from manim_studio.editor.config import (
    AUDIO_DIR,
    ALLOWED_AUDIO_EXTENSIONS,
    ESCENAS_DIR,
    MAX_UPLOAD_BYTES,
    MEDIA_DIR,
    PLANTILLAS_DIR,
    VAR_DIR,
)
from manim_studio.editor.security import UnsafePathError, safe_join

MAX_TEXT_BYTES = 2 * 1024 * 1024
TEXT_EXTENSIONS = {".py", ".txt", ".md", ".json", ".toml", ".cfg", ".ini"}
IGNORED_DIRS = {"__pycache__", ".git", ".venv", "node_modules"}

USER_TEMPLATES_DIR = VAR_DIR / "plantillas"
# Los archivos del proyecto son propiedad del usuario: se pueden añadir,
# renombrar y borrar desde el árbol.
PROTECTED_FILES: set[Path] = set()

# (raíz, editable) tal como se muestra en el árbol del frontend. La entrada
# `escenas` se reapunta al proyecto activo mediante `set_project()`.
ROOTS: dict[str, tuple[Path, bool]] = {
    "escenas": (ESCENAS_DIR, True),
    "plantillas": (PLANTILLAS_DIR, False),
    "mis-plantillas": (USER_TEMPLATES_DIR, True),
    "audios": (AUDIO_DIR, True),
    "media": (MEDIA_DIR, False),
}

SYSTEM_TEMPLATE_PATHS = {
    "biseccion": "plantillas/analisis_numerico/Bisección.py",
    "regla_falsa": "plantillas/analisis_numerico/Regla falsa.py",
    "newton_raphson": "plantillas/analisis_numerico/Newton-Raphson.py",
    "derivada_limite": "plantillas/calculo_diferencial/Derivada límite.py",
    "integral": "plantillas/calculo_diferencial/Integral.py",
    "serie_taylor": "plantillas/calculo_diferencial/Serie de Taylor.py",
    "curva_polinomica": "plantillas/algebra_geometria/Curva polinómica.py",
    "hud_algebra": "plantillas/algebra_geometria/HUD álgebra.py",
    "pasos_algebraicos": "plantillas/algebra_geometria/Pasos algebráicos.py",
    "serie_fourier": "plantillas/ecuaciones_diferenciales/Serie de Fourier.py",
    "purga_ciclo_vida": "plantillas/control_ciclo_vida/Purga ciclo de vida.py",
    "simplex": "plantillas/investigacion_operaciones/Simplex.py",
}

BUILTIN_TEMPLATES = [
    ("biseccion", "Bisección", "Análisis numérico"),
    ("regla_falsa", "Regla falsa", "Análisis numérico"),
    ("newton_raphson", "Newton-Raphson", "Análisis numérico"),
    ("derivada_limite", "Derivada límite", "Cálculo diferencial"),
    ("integral", "Integral", "Cálculo diferencial"),
    ("serie_taylor", "Serie de Taylor", "Cálculo diferencial"),
    ("curva_polinomica", "Curva polinómica", "Álgebra y geometría"),
    ("hud_algebra", "HUD álgebra", "Álgebra y geometría"),
    ("pasos_algebraicos", "Pasos algebraicos", "Archivos de trabajo"),
    ("serie_fourier", "Serie de Fourier", "Ecuaciones diferenciales"),
    ("purga_ciclo_vida", "Purga de ciclo de vida", "Control y ciclo de vida"),
    ("simplex", "Simplex", "Investigación de operaciones"),
]


class WorkspaceError(ValueError):
    """Error de validación de una operación del espacio de trabajo."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def _slug(value: str) -> str:
    text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^A-Za-z0-9_-]+", "_", text).strip("_")
    return text[:80] or "plantilla"


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _modified(path: Path) -> str:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    except OSError:
        return ""


def current_project() -> str:
    """Slug del proyecto que está usando el workspace en este momento."""

    return projects.active_slug()


def set_project(slug: str | None = None) -> str:
    """Apunta la raíz `escenas` al proyecto indicado (o al activo)."""

    fallback = projects.active_slug()
    candidate = str(slug).strip() if slug else fallback
    selected = fallback
    if candidate:
        try:
            if projects.project_dir(candidate).is_dir():
                selected = candidate
        except projects.ProjectError:
            pass
    base = projects.scenes_dir(selected) if selected else ESCENAS_DIR
    ROOTS["escenas"] = (base, True)
    return selected


def set_system_templates_unlocked(unlocked: bool) -> bool:
    settings = projects.update_settings({"unlockSystemTemplates": bool(unlocked)})
    ROOTS["plantillas"] = (PLANTILLAS_DIR, settings["unlockSystemTemplates"])
    return settings["unlockSystemTemplates"]


def apply_saved_context() -> None:
    """Carga el proyecto activo y los ajustes persistidos al iniciar."""

    set_project()
    settings = projects.get_settings()
    ROOTS["plantillas"] = (PLANTILLAS_DIR, settings["unlockSystemTemplates"])


def resolve(relative: str) -> tuple[Path, bool, str]:
    """Devuelve ``(ruta, editable, nombre_de_raíz)`` para una ruta pública."""

    raw = (relative or "").strip().replace("\\", "/").lstrip("/")
    parts = PurePosixPath(raw).parts
    if not parts:
        raise WorkspaceError(400, "Debes indicar una ruta.")
    root_name = parts[0]
    if root_name not in ROOTS:
        raise WorkspaceError(400, f"Raíz no permitida: {root_name}")
    base, writable = ROOTS[root_name]
    try:
        target = safe_join(base, "/".join(parts[1:]))
    except UnsafePathError as exc:
        raise WorkspaceError(400, str(exc)) from exc
    return target, writable, root_name


def public_path(path: Path, root_name: str) -> str:
    base = ROOTS[root_name][0]
    try:
        relative = path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        relative = path.name
    return f"{root_name}/{relative}" if relative else root_name


def _node(path: Path, root_name: str, writable: bool) -> dict:
    is_dir = path.is_dir()
    return {
        "path": public_path(path, root_name),
        "name": path.name or root_name,
        "type": "folder" if is_dir else "file",
        "writable": writable,
        "size": 0 if is_dir else path.stat().st_size,
        "modified": _modified(path),
    }


def tree() -> dict:
    roots: list[dict] = []
    total = 0
    for name, (base, writable) in ROOTS.items():
        base.mkdir(parents=True, exist_ok=True)
        children: list[dict] = []

        def walk(folder: Path, depth: int) -> list[dict]:
            nonlocal total
            items: list[dict] = []
            try:
                entries = sorted(os.scandir(folder), key=lambda entry: entry.name.lower())
            except OSError:
                return items
            for entry in entries:
                if total >= 400:
                    return items
                if entry.name.startswith(".") or entry.name in IGNORED_DIRS:
                    continue
                path = Path(entry.path)
                if entry.is_dir():
                    items.append({**_node(path, name, writable), "children": walk(path, depth + 1)})
                elif entry.is_file():
                    if path.suffix.lower() not in TEXT_EXTENSIONS | ALLOWED_AUDIO_EXTENSIONS | {".mp4", ".webm"}:
                        continue
                    items.append(_node(path, name, writable))
                total += 1
            return items

        children = walk(base, 0)
        roots.append(
            {
                "id": name,
                "name": {
                    "escenas": "Proyecto",
                    "plantillas": "Plantillas del sistema",
                    "mis-plantillas": "Mis plantillas",
                    "audios": "Audios",
                    "media": "Videos generados",
                }[name],
                "writable": writable,
                "children": children,
            }
        )
    return {"roots": roots}


def read(relative: str) -> dict:
    path, writable, root_name = resolve(relative)
    if not path.is_file():
        raise WorkspaceError(404, "Archivo no encontrado.")
    if path.suffix.lower() not in TEXT_EXTENSIONS:
        raise WorkspaceError(400, "Este archivo no es editable como texto.")
    data = path.read_bytes()
    if len(data) > MAX_TEXT_BYTES:
        raise WorkspaceError(413, "El archivo es demasiado grande para editarlo en el navegador.")
    try:
        code = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WorkspaceError(400, "El archivo no es UTF-8 válido.") from exc
    return {
        "path": public_path(path, root_name),
        "code": code,
        "sha256": _hash(data),
        "size": len(data),
        "modified": _modified(path),
        "writable": writable,
        "protected": path.resolve() in PROTECTED_FILES,
    }


def write(relative: str, code: str, expected_sha: str | None = None) -> dict:
    path, writable, root_name = resolve(relative)
    if not writable:
        raise WorkspaceError(403, "Esta carpeta es de solo lectura.")
    if path.is_dir():
        raise WorkspaceError(400, "La ruta corresponde a una carpeta.")
    if path.suffix.lower() not in TEXT_EXTENSIONS:
        raise WorkspaceError(400, f"Extensión no editable: {path.suffix}")

    current = path.read_bytes() if path.is_file() else b""
    if expected_sha and _hash(current) != expected_sha:
        raise WorkspaceError(409, "El archivo cambió en disco desde que lo abriste. Recárgalo antes de guardar.")

    data = code.encode("utf-8")
    if len(data) > MAX_TEXT_BYTES:
        raise WorkspaceError(413, "El contenido supera el límite de 2 MB.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return {
        "path": public_path(path, root_name),
        "sha256": _hash(data),
        "size": len(data),
        "modified": _modified(path),
        "saved": True,
    }


def create(relative: str, kind: str = "file") -> dict:
    path, writable, root_name = resolve(relative)
    if not writable:
        raise WorkspaceError(403, "Esta carpeta es de solo lectura.")
    if kind not in {"file", "folder"}:
        raise WorkspaceError(400, "Tipo no soportado (usa 'file' o 'folder').")
    if not path.name or path.name in {"..", "."}:
        raise WorkspaceError(400, "Nombre no válido.")
    if path.exists():
        raise WorkspaceError(409, "Ya existe un archivo o carpeta con ese nombre.")
    if kind == "file" and path.suffix.lower() not in TEXT_EXTENSIONS:
        raise WorkspaceError(400, "Extensión no permitida. Usa .py, .txt, .md, .json, .toml, .cfg o .ini.")
    path.parent.mkdir(parents=True, exist_ok=True)
    if kind == "folder":
        path.mkdir()
    else:
        path.write_text("", encoding="utf-8")
    return _node(path, root_name, writable)


def move(source: str, destination: str) -> dict:
    src, src_writable, src_root = resolve(source)
    dst, dst_writable, dst_root = resolve(destination)
    if not src_writable or not dst_writable:
        raise WorkspaceError(403, "Esta operación requiere una carpeta editable.")
    if src_root != dst_root:
        raise WorkspaceError(400, "No se puede mover entre raíces distintas.")
    if not src.exists():
        raise WorkspaceError(404, "Origen no encontrado.")
    if dst.exists():
        raise WorkspaceError(409, "Ya existe un destino con ese nombre.")
    if dst.parent != src.parent:
        dst.parent.mkdir(parents=True, exist_ok=True)
    src.rename(dst)
    return _node(dst, dst_root, dst_writable)


def delete(relative: str) -> dict:
    path, writable, root_name = resolve(relative)
    if not writable:
        raise WorkspaceError(403, "Esta carpeta es de solo lectura.")
    if not path.exists():
        raise WorkspaceError(404, "Archivo o carpeta no encontrado.")
    if path.resolve() in PROTECTED_FILES:
        raise WorkspaceError(400, "Este archivo es necesario para ejecutar el motor y no se puede borrar.")
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
    return {"deleted": public_path(path, root_name)}


def upload_audio(name: str, data_b64: str) -> dict:
    clean_name = os.path.basename((name or "").replace("\\", "/"))
    if not clean_name:
        raise WorkspaceError(400, "Debes indicar el nombre del audio.")
    if Path(clean_name).suffix.lower() not in ALLOWED_AUDIO_EXTENSIONS:
        raise WorkspaceError(400, "Formato de audio no permitido.")
    try:
        data = base64.b64decode(data_b64 or "", validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise WorkspaceError(400, "El audio recibido no es base64 válido.") from exc
    if not data:
        raise WorkspaceError(400, "El audio está vacío.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise WorkspaceError(413, "El audio supera el tamaño máximo permitido.")
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    target = safe_join(AUDIO_DIR, clean_name)
    target.write_bytes(data)
    return _node(target, "audios", True)


def templates() -> dict:
    items = [
        {
            "id": template_id,
            "name": name,
            "category": category,
            "origin": "motor",
            "path": SYSTEM_TEMPLATE_PATHS.get(template_id, f"plantillas/{template_id}"),
            "source": f"/api/get_template?id={template_id}",
        }
        for template_id, name, category in BUILTIN_TEMPLATES
    ]
    USER_TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(USER_TEMPLATES_DIR.glob("*.py")):
        items.append(
            {
                "id": f"user:{_slug(path.stem)}",
                "name": path.stem.replace("_", " ").title(),
                "category": "Mis plantillas",
                "origin": "user",
                "path": public_path(path, "mis-plantillas"),
                "source": "/api/workspace/files/read?path="
                + quote(public_path(path, "mis-plantillas"), safe=""),
            }
        )
    return {"templates": items}


def create_template(name: str, code: str) -> dict:
    import ast

    clean_name = (name or "").strip()
    if not clean_name:
        raise WorkspaceError(400, "Ponle un nombre a la plantilla.")
    if len(code.encode("utf-8")) > MAX_TEXT_BYTES:
        raise WorkspaceError(413, "La plantilla es demasiado grande.")
    try:
        ast.parse(code)
    except SyntaxError as exc:
        raise WorkspaceError(422, f"El código no es Python válido: {exc}") from exc

    USER_TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{_slug(clean_name)}.py"
    target = safe_join(USER_TEMPLATES_DIR, filename)
    if target.exists():
        raise WorkspaceError(409, "Ya existe una plantilla con ese nombre.")
    target.write_text(code, encoding="utf-8")
    return {
        "id": f"user:{_slug(clean_name)}",
        "name": clean_name,
        "category": "Mis plantillas",
        "origin": "user",
        "path": public_path(target, "mis-plantillas"),
        "source": "/api/workspace/files/read?path="
        + quote(public_path(target, "mis-plantillas"), safe=""),
    }
