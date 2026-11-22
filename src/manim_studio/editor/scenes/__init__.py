"""Runtimes de escena del editor.

Cada módulo recibe el IR ya validado y construye la animación con
`AnimadorGrafico`. El código generado solo importa estos runtimes.
"""

from manim_studio.editor.scenes.biseccion import construir_biseccion

__all__ = ["construir_biseccion"]
