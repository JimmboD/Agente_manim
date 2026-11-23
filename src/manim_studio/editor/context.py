"""Construcción del contexto adicional para el asistente de código.

El cliente solo envía rutas; el servidor resuelve, valida y recorta los
archivos. El buffer del editor nunca se sustituye por contenido del contexto.
"""

from __future__ import annotations

import os
from pathlib import Path

from manim_studio.editor import workspace

MODES = {"buffer", "files", "folder", "project"}
MAX_CONTEXT_FILES = 20
MAX_FILE_CHARS = 12_000
MAX_CONTEXT_CHARS = 40_000
EXCLUDED_DIRS = workspace.IGNORED_DIRS | {"partial_movie_files"}


class ContextError(workspace.WorkspaceError):
    """Error al resolver el contexto solicitado."""


def _is_inside(path: Path, base: Path) -> bool:
    try:
        resolved_base = str(base.resolve())
        resolved_path = str(path.resolve())
        return os.path.commonpath([resolved_base, resolved_path]) == resolved_base
    except (OSError, ValueError):
        return False


def _expand_folder(path: Path, root_name: str) -> list[str]:
    base = workspace.ROOTS[root_name][0]
    if not _is_inside(path, base):
        raise ContextError(400, "La carpeta está fuera de la raíz permitida.")
    candidates: list[str] = []
    for child in sorted(path.rglob("*")):
        if not child.is_file():
            continue
        if any(part in EXCLUDED_DIRS or part.startswith(".") for part in child.relative_to(path).parts[:-1]):
            continue
        if child.suffix.lower() not in workspace.TEXT_EXTENSIONS:
            continue
        candidates.append(workspace.public_path(child, root_name))
    return candidates


def _collect_paths(mode: str, raw_paths: object) -> list[str]:
    if mode == "buffer":
        return []
    if mode == "project":
        base = workspace.ROOTS["escenas"][0]
        return _expand_folder(base, "escenas")
    if not isinstance(raw_paths, list):
        raise ContextError(400, "El contexto debe incluir una lista de rutas.")

    paths: list[str] = []
    for raw in raw_paths:
        target, _writable, root_name = workspace.resolve(str(raw or ""))
        if mode == "folder":
            if not target.is_dir():
                raise ContextError(400, f"No es una carpeta: {raw}")
            paths.extend(_expand_folder(target, root_name))
        else:
            if not target.is_file():
                raise ContextError(400, f"No es un archivo: {raw}")
            if target.suffix.lower() not in workspace.TEXT_EXTENSIONS:
                continue
            paths.append(workspace.public_path(target, root_name))
    return paths


def build_context(
    path: str,
    mode: str | None = None,
    raw_paths: object = None,
) -> dict:
    """Devuelve archivos de solo lectura ya resueltos, ordenados y recortados."""

    selected = str(mode or "buffer").strip().lower()
    if selected not in MODES:
        raise ContextError(400, f"Modo de contexto no soportado: {mode}")

    active, _writable, _root = workspace.resolve(path)
    candidates = _collect_paths(selected, raw_paths)

    files: list[dict] = []
    seen: set[str] = set()
    total = 0
    omitted = 0
    truncated = False

    for public in candidates:
        if len(files) >= MAX_CONTEXT_FILES:
            omitted += 1
            continue
        target, _writable, root_name = workspace.resolve(public)
        if target.resolve() == active.resolve():
            continue
        if public in seen:
            continue
        seen.add(public)

        document = workspace.read(public)
        code = str(document.get("code", ""))
        if len(code) > MAX_FILE_CHARS:
            code = code[:MAX_FILE_CHARS]
            item_truncated = True
            truncated = True
        else:
            item_truncated = False

        if total + len(code) > MAX_CONTEXT_CHARS:
            omitted += 1
            continue

        total += len(code)
        files.append(
            {
                "path": workspace.public_path(target, root_name),
                "code": code,
                "truncated": item_truncated,
            }
        )

    return {
        "mode": selected,
        "files": files,
        "chars": total,
        "omitted": omitted,
        "truncated": truncated,
    }
