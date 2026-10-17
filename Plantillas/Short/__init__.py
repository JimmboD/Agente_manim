"""
Paquete Plantillas.Short
Módulos para la generación, análisis temporal y escalado de cadencia
de animaciones matemáticas optimizadas para formatos de video vertical / corto (Shorts, Reels, TikTok).
"""

from Plantillas.Short.tiempo import (
    calcular_tiempo_maximo,
    desglosar_tiempo_maximo,
    verificar_duracion_short,
    calcular_vector_tiempos,
    escalar_cadencia,
    VectorTiempos,
    ORDEN_CLAVES_BISECCION,
    ORDEN_CLAVES_REGLA_FALSA,
    ORDEN_CLAVES_NEWTON_RAPHSON,
    TIEMPOS_DEFECTO_BISECCION,
    TIEMPOS_DEFECTO_REGLA_FALSA,
    TIEMPOS_DEFECTO_NEWTON_RAPHSON,
)

from Plantillas.Short.generador_short import (
    generar_codigo_short,
    procesar_funcion_simbolica,
    normalizar_expresion_matematica
)

__all__ = [
    "calcular_tiempo_maximo",
    "desglosar_tiempo_maximo",
    "verificar_duracion_short",
    "calcular_vector_tiempos",
    "escalar_cadencia",
    "VectorTiempos",
    "generar_codigo_short",
    "procesar_funcion_simbolica",
    "normalizar_expresion_matematica",
    "ORDEN_CLAVES_BISECCION",
    "ORDEN_CLAVES_REGLA_FALSA",
    "ORDEN_CLAVES_NEWTON_RAPHSON",
    "TIEMPOS_DEFECTO_BISECCION",
    "TIEMPOS_DEFECTO_REGLA_FALSA",
    "TIEMPOS_DEFECTO_NEWTON_RAPHSON",
]
