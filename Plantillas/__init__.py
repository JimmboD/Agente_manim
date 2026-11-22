"""
Paquete principal de Plantillas para Manim Studio.
Expone las plantillas y métodos matemáticos para ser utilizados e importados directamente.
"""

import os
import sys
import importlib.util

# Cargar dinámicamente el módulo Simplex desde 'Investigacion de operaciones'
_dir_actual = os.path.dirname(__file__)
_simplex_path = os.path.join(_dir_actual, "Investigacion de operaciones", "Simplex.py")

if os.path.isfile(_simplex_path):
    _spec = importlib.util.spec_from_file_location("Plantillas.Investigacion_de_operaciones.Simplex", _simplex_path)
    _simplex_mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_simplex_mod)

    # Exportar símbolos a nivel de Plantillas
    SimplexSolver = _simplex_mod.SimplexSolver
    SimplexScene = _simplex_mod.SimplexScene
    SimplexAnimation = _simplex_mod.SimplexAnimation
    animar_simplex = _simplex_mod.animar_simplex

    # Registrar en sys.modules para permitir imports con guion bajo
    sys.modules["Plantillas.Investigacion_de_operaciones"] = _simplex_mod
    sys.modules["Plantillas.Investigacion_de_operaciones.Simplex"] = _simplex_mod

__all__ = [
    "SimplexSolver",
    "SimplexScene",
    "SimplexAnimation",
    "animar_simplex",
]
