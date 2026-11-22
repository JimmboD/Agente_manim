"""Plantillas reutilizables del motor Manim.

Las plantillas numéricas y de álgebra se sirven como código fuente al editor;
los únicos subpaquetes importables son ``short`` e
``investigacion_operaciones``.
"""

from manim_studio.motor.plantillas.investigacion_operaciones import (
    A_RESTRICCIONES,
    B_LIMITES,
    C_OBJETIVO,
    T,
    SimplexAnimation,
    SimplexScene,
    SimplexSolver,
    animar_simplex,
)

__all__ = [
    "SimplexSolver",
    "SimplexScene",
    "SimplexAnimation",
    "animar_simplex",
    "C_OBJETIVO",
    "A_RESTRICCIONES",
    "B_LIMITES",
    "T",
]
