"""
Módulo alias para 'Investigacion de operaciones' sin espacios en el nombre.
Permite importaciones naturales en Python:
    from Plantillas.Investigacion_de_operaciones import animar_simplex, SimplexScene
    from Plantillas.Investigacion_de_operaciones.Simplex import animar_simplex
"""

import os
import sys
import importlib.util

_dir_actual = os.path.dirname(__file__)
_simplex_path = os.path.join(_dir_actual, "Investigacion de operaciones", "Simplex.py")

_spec = importlib.util.spec_from_file_location("Plantillas.Investigacion_de_operaciones.Simplex", _simplex_path)
Simplex = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(Simplex)

SimplexSolver = Simplex.SimplexSolver
SimplexScene = Simplex.SimplexScene
SimplexAnimation = Simplex.SimplexAnimation
animar_simplex = Simplex.animar_simplex
C_OBJETIVO = Simplex.C_OBJETIVO
A_RESTRICCIONES = Simplex.A_RESTRICCIONES
B_LIMITES = Simplex.B_LIMITES
T = Simplex.T

__all__ = [
    "Simplex",
    "SimplexSolver",
    "SimplexScene",
    "SimplexAnimation",
    "animar_simplex",
    "C_OBJETIVO",
    "A_RESTRICCIONES",
    "B_LIMITES",
    "T",
]
