"""Generación determinista de la escena Python a partir del IR.

El código generado es deliberadamente delgado: incrusta el IR y delega en un
runtime de escena (`manim_studio/editor/scenes/...`). Así el LLM nunca necesita
reescribir el algoritmo completo y el resultado es reproducible.
"""

from __future__ import annotations

import ast
import difflib

_HEADER = '''"""Escena generada por Manim Studio Editor.

No edites este archivo a mano: la fuente de verdad es el IR del proyecto.
"""

import sys

from manim_studio.editor.scenes.biseccion import construir_biseccion

'''

_FOOTER = '''

if __name__ == "__main__":
    construir_biseccion(IR)
'''

_FORBIDDEN_NAMES = {
    "eval", "exec", "open", "__import__", "compile", "globals", "locals",
    "getattr", "setattr", "delattr", "input", "breakpoint",
}
_FORBIDDEN_MODULES = {"os", "subprocess", "socket", "shutil", "pathlib", "pickle"}


def generate_code(ir: dict) -> str:
    """Devuelve un script Python autocontenido que construye la escena."""

    if not isinstance(ir, dict):
        raise TypeError("El IR debe ser un diccionario.")

    body = f"IR = {ir!r}\n"
    return _HEADER + body + _FOOTER


def validate_generated_code(code: str) -> None:
    """Comprueba que el script generado solo hace lo permitido."""

    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        raise ValueError(f"El código generado no parsea: {exc}") from exc

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in _FORBIDDEN_MODULES:
                    raise ValueError(f"Import prohibido: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root in _FORBIDDEN_MODULES:
                raise ValueError(f"Import prohibido: {node.module}")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in _FORBIDDEN_NAMES:
                raise ValueError(f"Llamada prohibida: {node.func.id}")
        elif isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name) and node.value.id in _FORBIDDEN_MODULES:
                raise ValueError(f"Acceso prohibido: {node.value.id}.{node.attr}")


def code_diff(previous: str, current: str, *, filename: str = "scene.py") -> str:
    """Diff unificado para mostrar al usuario qué cambió."""

    return "".join(
        difflib.unified_diff(
            (previous or "").splitlines(keepends=True),
            (current or "").splitlines(keepends=True),
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
        )
    )
