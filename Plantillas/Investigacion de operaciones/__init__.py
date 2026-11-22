"""
Paquete Plantillas.Investigacion de operaciones
Módulos y plantillas de optimización matemática e Investigación de Operaciones.
"""

from .Simplex import (
    SimplexSolver,
    SimplexScene,
    SimplexAnimation,
    animar_simplex,
    C_OBJETIVO,
    A_RESTRICCIONES,
    B_LIMITES,
    T,
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
