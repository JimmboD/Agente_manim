"""Plantillas que despliegan varios archivos en el proyecto activo.

«Pasos algebraicos» necesita un script Python y un archivo ``.txt`` de
ecuaciones. Desplegar ambos juntos evita que el usuario edite el ``.txt`` sin
que exista el runner que lo consume.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from manim_studio.editor import workspace
from manim_studio.editor.config import PLANTILLAS_DIR

BUNDLE_ID = "pasos_algebraicos"
SCRIPT_PATH = "escenas/pasos_algebraicos.py"
TEXT_PATH = "escenas/pasos_algebraicos.txt"

BUNDLE_IDS = {BUNDLE_ID}

SCRIPT_CONTENT = '''# -*- coding: utf-8 -*-
"""Animación de pasos algebraicos a partir de un archivo de ecuaciones."""

from pathlib import Path

from manim_studio.motor.planos.generar_plano import AnimadorGrafico

PASOS_PATH = Path(__file__).with_name("pasos_algebraicos.txt")


if __name__ == "__main__":
    escena = AnimadorGrafico()
    escena.insertar_algebra(
        str(PASOS_PATH),
        tiempo_animacion=1.5,
        tiempo_espera=2.0,
    )
    escena.desvanecer_todo(tiempo_animacion=1.5)
    escena.render(previsualizar=True)
'''

FALLBACK_TEXT = r"""$$\textcolor{yellow}{y} = \frac{f(b) - f(a)}{b - a} \textcolor{yellow}{x} + \textcolor{yellow}{b}$$
$$y = \frac{f(b) - f(a)}{b - a} x + \textcolor{yellow}{b}$$
$$f(c) = \frac{f(b) - f(a)}{b - a} c + \textcolor{yellow}{b}$$
"""


class TemplateConflictError(workspace.WorkspaceError):
    """Los archivos ya existen y el cliente no confirmó la sobrescritura."""

    def __init__(self, conflicts: list[dict]):
        super().__init__(
            409,
            "Ya existen archivos de esta plantilla en el proyecto. "
            "Confirma la sobrescritura antes de continuar.",
        )
        self.conflicts = conflicts

    @property
    def expected_shas(self) -> dict[str, str]:
        return {item["path"]: item["sha256"] for item in self.conflicts}


def is_bundle(template_id: str) -> bool:
    return str(template_id or "").strip() in BUNDLE_IDS


def _seed_text() -> str:
    source = PLANTILLAS_DIR / "algebra_geometria" / "Pasos algebráicos.txt"
    try:
        return source.read_text(encoding="utf-8")
    except OSError:
        return FALLBACK_TEXT


def files_for(template_id: str) -> dict[str, str]:
    """Contenido de cada archivo del bundle, indexado por ruta pública."""

    if not is_bundle(template_id):
        raise workspace.WorkspaceError(404, "Plantilla multiarchivo no encontrada.")
    return {
        SCRIPT_PATH: SCRIPT_CONTENT,
        TEXT_PATH: _seed_text(),
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def deploy(
    template_id: str,
    *,
    overwrite: bool = False,
    expected_shas: dict[str, str] | None = None,
    project: str | None = None,
) -> dict:
    """Crea (o sobrescribe con confirmación) los archivos del bundle."""

    files = files_for(template_id)
    if project:
        workspace.set_project(str(project))

    existing: list[dict] = []
    for public in files:
        target, _writable, _root = workspace.resolve(public)
        if target.is_file():
            existing.append({"path": public, "sha256": _sha256(target)})

    if existing:
        provided = expected_shas if isinstance(expected_shas, dict) else {}
        if not overwrite:
            raise TemplateConflictError(existing)
        stale = [
            item for item in existing if provided.get(item["path"]) != item["sha256"]
        ]
        if stale:
            raise TemplateConflictError(existing)

    created: list[dict] = []
    existing_paths = {item["path"] for item in existing}
    for public, content in files.items():
        expected = provided.get(public) if public in existing_paths else None
        result = workspace.write(public, content, expected)
        created.append(
            {
                "path": result["path"],
                "sha256": result["sha256"],
                "size": result["size"],
                "action": "overwritten" if public in existing_paths else "created",
            }
        )

    return {
        "template": str(template_id),
        "project": workspace.current_project(),
        "files": created,
        "open": SCRIPT_PATH,
    }
