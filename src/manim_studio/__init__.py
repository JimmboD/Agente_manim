"""Manim Studio: editor de escenas y motor de animación matemática.

La raíz del proyecto se expone aquí para que los módulos de dominio no
dependan de su propia ubicación dentro de ``src/``.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAQUETE_DIR = Path(__file__).resolve().parent

__all__ = ["ROOT", "PAQUETE_DIR"]
