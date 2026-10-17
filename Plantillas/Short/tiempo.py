"""
================================================================================
MÓDULO: tiempo.py (Plantillas/Short)
Cálculo analítico, desglose y escalado de cadencia para métodos numéricos
(Bisección, Regla Falsa y Newton-Raphson) en formatos de video corto (Shorts / Reels / TikTok).
================================================================================
"""

from typing import Dict, Any, Optional, Union, List, Tuple


# ==============================================================================
# 1. TIEMPOS PREDEFINIDOS ESTÁNDAR POR MÉTODO
# ==============================================================================

TIEMPOS_SETUP_BASE = {
    "T_SETUP_PLANO": 1.5,       # Create(plano)
    "T_SETUP_CURVA": 1.0,       # Create(grafica)
    "T_SETUP_LABEL_ANIM": 1.0,  # Write(label_funcion)
    "T_SETUP_LABEL_ESPERA": 1.0 # wait tras label_funcion
}

# Claves ordenadas en el mismo orden que aparecen en las plantillas .py
ORDEN_CLAVES_BISECCION: List[str] = [
    "T_PUNTOS_INI_ANIM", "T_PUNTOS_INI_ESPERA",
    "T_HUD_ANIM", "T_HUD_ESPERA",
    "T_PROY_PUNTO_ANIM", "T_PROY_PUNTO_ESPERA",
    "T_PROY_LINEA_ANIM", "T_PROY_LINEA_ESPERA",
    "T_LIMPIEZA_LINEA_ANIM", "T_LIMPIEZA_LINEA_ESPERA",
    "T_LIMPIEZA_PUNTO_ANIM", "T_LIMPIEZA_PUNTO_ESPERA",
    "T_MOVIMIENTO_CURVA_ANIM", "T_MOVIMIENTO_CURVA_ESPERA",
    "T_FINAL_ANIM", "T_FINAL_ESPERA"
]

ORDEN_CLAVES_REGLA_FALSA: List[str] = [
    "T_PUNTOS_INI_ANIM", "T_PUNTOS_INI_ESPERA",
    "T_SECANTE_INI_ANIM", "T_SECANTE_INI_ESPERA",
    "T_HUD_ANIM", "T_HUD_ESPERA",
    "T_PROY_PUNTO_ANIM", "T_PROY_PUNTO_ESPERA",
    "T_PROY_LINEA_ANIM", "T_PROY_LINEA_ESPERA",
    "T_LIMPIEZA_LINEA_ANIM", "T_LIMPIEZA_LINEA_ESPERA",
    "T_LIMPIEZA_PUNTO_ANIM", "T_LIMPIEZA_PUNTO_ESPERA",
    "T_CONVERGENCIA_ANIM", "T_CONVERGENCIA_ESPERA",
    "T_FINAL_ANIM", "T_FINAL_ESPERA"
]

ORDEN_CLAVES_NEWTON_RAPHSON: List[str] = [
    "T_PUNTO_INI_ANIM", "T_PUNTO_INI_ESPERA",
    "T_TANGENTE_INI_ANIM", "T_TANGENTE_INI_ESPERA",
    "T_HUD_ANIM", "T_HUD_ESPERA",
    "T_PROY_PUNTO_ANIM", "T_PROY_PUNTO_ESPERA",
    "T_PROY_LINEA_ANIM", "T_PROY_LINEA_ESPERA",
    "T_TRANSICION_PARALELO_ANIM", "T_TRANSICION_PARALELO_ESPERA",
    "T_LIMPIEZA_LINEA_ANIM", "T_LIMPIEZA_LINEA_ESPERA",
    "T_LIMPIEZA_PUNTO_ANIM", "T_LIMPIEZA_PUNTO_ESPERA",
    "T_FINAL_ANIM", "T_FINAL_ESPERA"
]

ORDEN_CLAVES_SERIE_TAYLOR: List[str] = [
    "T_PUNTO_INI_ANIM", "T_PUNTO_INI_ESPERA",
    "T_HUD_ANIM", "T_HUD_ESPERA",
    "T_TAYLOR_INI_ANIM", "T_TAYLOR_INI_ESPERA",
    "T_TAYLOR_TRANSFORM_ANIM", "T_TAYLOR_TRANSFORM_ESPERA",
    "T_FINAL_ANIM", "T_FINAL_ESPERA"
]

TIEMPOS_DEFECTO_BISECCION: Dict[str, float] = {
    **TIEMPOS_SETUP_BASE,
    "T_PUNTOS_INI_ANIM": 0.5,
    "T_PUNTOS_INI_ESPERA": 0.1,
    "T_HUD_ANIM": 1.0,
    "T_HUD_ESPERA": 1.0,
    "T_HUD_SALIDA": 0.5,        # FadeOut automático del HUD al terminar la iteración
    "T_PROY_PUNTO_ANIM": 0.5,
    "T_PROY_PUNTO_ESPERA": 1.0,
    "T_PROY_LINEA_ANIM": 0.8,
    "T_PROY_LINEA_ESPERA": 1.0,
    "T_LIMPIEZA_LINEA_ANIM": 0.5,
    "T_LIMPIEZA_LINEA_ESPERA": 0.1,
    "T_LIMPIEZA_PUNTO_ANIM": 0.5,
    "T_LIMPIEZA_PUNTO_ESPERA": 0.2,
    "T_MOVIMIENTO_CURVA_ANIM": 1.5,
    "T_MOVIMIENTO_CURVA_ESPERA": 1.0,
    "T_FINAL_ANIM": 2.0,
    "T_FINAL_ESPERA": 1.0,
}

TIEMPOS_DEFECTO_REGLA_FALSA: Dict[str, float] = {
    **TIEMPOS_SETUP_BASE,
    "T_PUNTOS_INI_ANIM": 0.5,
    "T_PUNTOS_INI_ESPERA": 0.1,
    "T_SECANTE_INI_ANIM": 1.0,    # Solo en iteración 1
    "T_SECANTE_INI_ESPERA": 1.0,  # Solo en iteración 1
    "T_HUD_ANIM": 1.0,
    "T_HUD_ESPERA": 1.0,
    "T_HUD_SALIDA": 0.5,
    "T_PROY_PUNTO_ANIM": 0.5,
    "T_PROY_PUNTO_ESPERA": 1.0,
    "T_PROY_LINEA_ANIM": 0.8,
    "T_PROY_LINEA_ESPERA": 1.0,
    "T_LIMPIEZA_LINEA_ANIM": 0.5,
    "T_LIMPIEZA_LINEA_ESPERA": 0.1,
    "T_LIMPIEZA_PUNTO_ANIM": 0.5,
    "T_LIMPIEZA_PUNTO_ESPERA": 0.2,
    "T_CONVERGENCIA_ANIM": 2.0,
    "T_CONVERGENCIA_ESPERA": 1.0,
    "T_FINAL_ANIM": 2.0,
    "T_FINAL_ESPERA": 1.0,
}

TIEMPOS_DEFECTO_NEWTON_RAPHSON: Dict[str, float] = {
    **TIEMPOS_SETUP_BASE,
    "T_PUNTO_INI_ANIM": 0.5,      # 1 solo punto ancla inicial
    "T_PUNTO_INI_ESPERA": 0.1,
    "T_TANGENTE_INI_ANIM": 1.0,   # Solo en iteración 1
    "T_TANGENTE_INI_ESPERA": 1.0, # Solo en iteración 1
    "T_HUD_ANIM": 1.0,
    "T_HUD_ESPERA": 1.0,
    "T_HUD_SALIDA": 0.5,
    "T_PROY_PUNTO_ANIM": 0.5,
    "T_PROY_PUNTO_ESPERA": 1.0,
    "T_PROY_LINEA_ANIM": 0.8,
    "T_PROY_LINEA_ESPERA": 1.0,
    "T_TRANSICION_PARALELO_ANIM": 2.0,
    "T_TRANSICION_PARALELO_ESPERA": 1.0,
    "T_LIMPIEZA_LINEA_ANIM": 0.5,
    "T_LIMPIEZA_LINEA_ESPERA": 0.1,
    "T_LIMPIEZA_PUNTO_ANIM": 0.5,
    "T_LIMPIEZA_PUNTO_ESPERA": 0.2,
    "T_FINAL_ANIM": 2.0,
    "T_FINAL_ESPERA": 1.0,
}

TIEMPOS_DEFECTO_SERIE_TAYLOR: Dict[str, float] = {
    **TIEMPOS_SETUP_BASE,
    "T_PUNTO_INI_ANIM": 0.5,      # Punto de anclaje blanco en (x0, f(x0))
    "T_PUNTO_INI_ESPERA": 0.2,
    "T_HUD_ANIM": 0.8,
    "T_HUD_ESPERA": 0.6,
    "T_HUD_SALIDA": 0.3,
    "T_TAYLOR_INI_ANIM": 1.2,     # Nacimiento de la curva grado 0
    "T_TAYLOR_INI_ESPERA": 0.5,
    "T_TAYLOR_TRANSFORM_ANIM": 1.4,# Deformación/Morphing de la curva en grados sucesivos
    "T_TAYLOR_TRANSFORM_ESPERA": 0.6,
    "T_FINAL_ANIM": 2.0,
    "T_FINAL_ESPERA": 1.0,
}


# ==============================================================================
# 2. CLASE VECTORIAL DE TIEMPOS
# ==============================================================================

class VectorTiempos(list):
    """
    Estructura vectorial que representa la lista ordenada de tiempos calculados
    para los pasos de una animación numérica.
    
    Permite:
    1. Desempaquetado e indexación posicional como lista o vector clásico:
       `t_pto_anim, t_pto_esp, t_hud_anim, ... = vector`
       `primer_tiempo = vector[0]`
    2. Acceso por clave como diccionario o atributo de objeto:
       `vector['T_HUD_ANIM']` o `vector.T_HUD_ANIM`
    3. Conversión a diccionario con `.to_dict()` o `.como_diccionario()`
    """

    def __init__(
        self,
        valores: List[float],
        claves: List[str],
        metodo: str,
        tiempo_objetivo: float,
        tiempo_estimado: float,
        factor_escalado: float,
        tiempos_completos: Optional[Dict[str, float]] = None
    ):
        super().__init__(valores)
        self.claves = list(claves)
        self.metodo = metodo
        self.tiempo_objetivo = tiempo_objetivo
        self.tiempo_estimado = tiempo_estimado
        self.factor_escalado = factor_escalado
        self._mapa = dict(zip(self.claves, valores))
        self.tiempos_completos = dict(tiempos_completos) if tiempos_completos else dict(self._mapa)

    def __getitem__(self, item: Union[int, slice, str]) -> Any:
        if isinstance(item, str):
            if item in self.tiempos_completos:
                return self.tiempos_completos[item]
            # Búsqueda flexible de clave
            item_norm = item.upper()
            if item_norm in self.tiempos_completos:
                return self.tiempos_completos[item_norm]
            if f"T_{item_norm}" in self.tiempos_completos:
                return self.tiempos_completos[f"T_{item_norm}"]
            raise KeyError(f"Clave de tiempo '{item}' no encontrada en VectorTiempos para {self.metodo}")
        return super().__getitem__(item)

    def __getattr__(self, name: str) -> float:
        if name in self.tiempos_completos:
            return self.tiempos_completos[name]
        name_norm = name.upper()
        if name_norm in self.tiempos_completos:
            return self.tiempos_completos[name_norm]
        if f"T_{name_norm}" in self.tiempos_completos:
            return self.tiempos_completos[f"T_{name_norm}"]
        raise AttributeError(f"'VectorTiempos' de {self.metodo} no tiene el atributo '{name}'")

    def to_dict(self, solo_claves_principales: bool = False) -> Dict[str, float]:
        """Retorna los tiempos como un diccionario {NOMBRE_CONSTANTE: valor}."""
        if solo_claves_principales:
            return dict(self._mapa)
        return dict(self.tiempos_completos)

    def como_diccionario(self, solo_claves_principales: bool = False) -> Dict[str, float]:
        """Alias en español para to_dict()."""
        return self.to_dict(solo_claves_principales=solo_claves_principales)

    def __repr__(self) -> str:
        items_str = ", ".join(f"{k}: {v}" for k, v in self._mapa.items())
        return f"VectorTiempos({self.metodo.upper()}, total={self.tiempo_estimado}s, factor={self.factor_escalado}x, [{items_str}])"


# ==============================================================================
# 3. FUNCIONES DE NORMALIZACIÓN Y AUXILIARES
# ==============================================================================

def _normalizar_metodo(metodo: Optional[str]) -> str:
    """Normaliza el nombre del método a una clave estándar."""
    m = (metodo or "").strip().lower()
    m = m.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
    m = m.replace("-", "_").replace(" ", "_")

    if not m or m in ["todos", "all", "*"]:
        return "todos"
    elif "bisec" in m:
        return "biseccion"
    elif "regla" in m or "falsa" in m:
        return "regla_falsa"
    elif "newton" in m or "raphson" in m or "rhapson" in m:
        return "newton_raphson"
    elif "taylor" in m or "serie" in m:
        return "serie_taylor"
    else:
        raise ValueError(
            f"Método '{metodo}' no reconocido. Métodos válidos: 'biseccion', 'regla_falsa', 'newton_raphson', 'serie_taylor', o 'todos'."
        )


def obtener_claves_metodo(metodo: str) -> List[str]:
    """Retorna la lista ordenada de claves de tiempo para el método dado."""
    metodo_norm = _normalizar_metodo(metodo)
    if metodo_norm == "biseccion":
        return list(ORDEN_CLAVES_BISECCION)
    elif metodo_norm == "regla_falsa":
        return list(ORDEN_CLAVES_REGLA_FALSA)
    elif metodo_norm == "newton_raphson":
        return list(ORDEN_CLAVES_NEWTON_RAPHSON)
    elif metodo_norm == "serie_taylor":
        return list(ORDEN_CLAVES_SERIE_TAYLOR)
    else:
        raise ValueError(f"Método desconocido para obtener claves: {metodo}")


def obtener_tiempos_defecto(metodo: str) -> Dict[str, float]:
    """Retorna una copia del diccionario de tiempos predefinidos para el método dado."""
    metodo_norm = _normalizar_metodo(metodo)
    if metodo_norm == "biseccion":
        return dict(TIEMPOS_DEFECTO_BISECCION)
    elif metodo_norm == "regla_falsa":
        return dict(TIEMPOS_DEFECTO_REGLA_FALSA)
    elif metodo_norm == "newton_raphson":
        return dict(TIEMPOS_DEFECTO_NEWTON_RAPHSON)
    elif metodo_norm == "serie_taylor":
        return dict(TIEMPOS_DEFECTO_SERIE_TAYLOR)
    else:
        raise ValueError(f"Método desconocido: {metodo}")


def _fusionar_tiempos(
    metodo_norm: str,
    tiempos_usuario: Optional[Dict[str, Any]] = None,
    kwargs_tiempos: Optional[Dict[str, Any]] = None
) -> Dict[str, float]:
    """
    Combina los tiempos predefinidos con los tiempos proporcionados por el usuario.
    """
    tiempos_finales = obtener_tiempos_defecto(metodo_norm)
    fuentes = []
    if tiempos_usuario and isinstance(tiempos_usuario, dict):
        fuentes.append(tiempos_usuario)
    if kwargs_tiempos:
        fuentes.append(kwargs_tiempos)

    for fuente in fuentes:
        for k, v in fuente.items():
            if v is None:
                continue

            if isinstance(v, dict):
                prefijo = k.upper()
                for sub_k, sub_v in v.items():
                    clave_candidata = f"T_{prefijo}_{sub_k.upper()}"
                    for key in tiempos_finales:
                        if key.replace("_", "").lower() == clave_candidata.replace("_", "").lower():
                            tiempos_finales[key] = float(sub_v)
            else:
                k_upper = k.upper()
                encontrado = False
                for key in tiempos_finales:
                    if key == k_upper or key == f"T_{k_upper}" or key.replace("_", "").lower() == k.replace("_", "").lower():
                        tiempos_finales[key] = float(v)
                        encontrado = True
                        break
                if not encontrado:
                    tiempos_finales[k_upper] = float(v)

    return tiempos_finales


# ==============================================================================
# 4. FUNCIONES DE CÁLCULO DE TIEMPO MÁXIMO Y DESGLOSE
# ==============================================================================

def calcular_tiempo_maximo(
    metodo: str,
    max_iteraciones: int,
    tiempos: Optional[Dict[str, Any]] = None,
    incluir_setup: bool = True,
    **kwargs
) -> float:
    """
    Calcula el tiempo total máximo en segundos que tardará una animación matemática
    de Manim para un método numérico dado, asumiendo que se ejecutan todas las iteraciones.
    """
    desglose = desglosar_tiempo_maximo(
        metodo=metodo,
        max_iteraciones=max_iteraciones,
        tiempos=tiempos,
        incluir_setup=incluir_setup,
        **kwargs
    )
    return desglose["tiempo_total_maximo"]


def desglosar_tiempo_maximo(
    metodo: str,
    max_iteraciones: int,
    tiempos: Optional[Dict[str, Any]] = None,
    incluir_setup: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    Genera un desglose detallado de todos los componentes temporales de la animación.
    """
    if max_iteraciones < 0:
        raise ValueError("max_iteraciones no puede ser negativo.")

    metodo_norm = _normalizar_metodo(metodo)
    if metodo_norm == "todos":
        raise ValueError("desglosar_tiempo_maximo requiere un método específico ('biseccion', 'regla_falsa' o 'newton_raphson').")

    t = _fusionar_tiempos(metodo_norm, tiempos, kwargs)

    # 1. Setup inicial
    if incluir_setup:
        t_plano = t.get("T_SETUP_PLANO", 1.5)
        t_curva = t.get("T_SETUP_CURVA", 1.0)
        t_label = t.get("T_SETUP_LABEL_ANIM", 1.0) + t.get("T_SETUP_LABEL_ESPERA", 1.0)
        tiempo_setup = t_plano + t_curva + t_label
    else:
        tiempo_setup = 0.0

    # 2. Cierre y desvanecimiento final
    tiempo_cierre = t.get("T_FINAL_ANIM", 2.0) + t.get("T_FINAL_ESPERA", 1.0)

    # 3. Cálculos específicos por método
    if metodo_norm == "biseccion":
        tiempo_estado_inicial = 2 * (t["T_PUNTOS_INI_ANIM"] + t["T_PUNTOS_INI_ESPERA"])
        t_hud = 4 * (t["T_HUD_ANIM"] + t["T_HUD_ESPERA"]) + t.get("T_HUD_SALIDA", 0.5)
        t_proy_punto = t["T_PROY_PUNTO_ANIM"] + t["T_PROY_PUNTO_ESPERA"]
        t_proy_linea = t["T_PROY_LINEA_ANIM"] + t["T_PROY_LINEA_ESPERA"]
        t_limp_linea = t["T_LIMPIEZA_LINEA_ANIM"] + t["T_LIMPIEZA_LINEA_ESPERA"]
        t_limp_punto = t["T_LIMPIEZA_PUNTO_ANIM"] + t["T_LIMPIEZA_PUNTO_ESPERA"]
        t_movimiento = t["T_MOVIMIENTO_CURVA_ANIM"] + t["T_MOVIMIENTO_CURVA_ESPERA"]
        
        tiempo_por_iteracion = t_hud + t_proy_punto + t_proy_linea + t_limp_linea + t_limp_punto + t_movimiento
        tiempo_iteraciones = max_iteraciones * tiempo_por_iteracion
        tiempo_extra_iteracion_1 = 0.0

    elif metodo_norm == "regla_falsa":
        tiempo_estado_inicial = 2 * (t["T_PUNTOS_INI_ANIM"] + t["T_PUNTOS_INI_ESPERA"])
        tiempo_extra_iteracion_1 = (t["T_SECANTE_INI_ANIM"] + t["T_SECANTE_INI_ESPERA"]) if max_iteraciones >= 1 else 0.0
        
        t_hud = 4 * (t["T_HUD_ANIM"] + t["T_HUD_ESPERA"]) + t.get("T_HUD_SALIDA", 0.5)
        t_proy_punto = t["T_PROY_PUNTO_ANIM"] + t["T_PROY_PUNTO_ESPERA"]
        t_proy_linea = t["T_PROY_LINEA_ANIM"] + t["T_PROY_LINEA_ESPERA"]
        t_limp_linea = t["T_LIMPIEZA_LINEA_ANIM"] + t["T_LIMPIEZA_LINEA_ESPERA"]
        t_limp_punto = t["T_LIMPIEZA_PUNTO_ANIM"] + t["T_LIMPIEZA_PUNTO_ESPERA"]
        t_convergencia = t["T_CONVERGENCIA_ANIM"] + t["T_CONVERGENCIA_ESPERA"]
        
        tiempo_por_iteracion = t_hud + t_proy_punto + t_proy_linea + t_limp_linea + t_limp_punto + t_convergencia
        tiempo_iteraciones = (max_iteraciones * tiempo_por_iteracion) + tiempo_extra_iteracion_1

    elif metodo_norm == "newton_raphson":
        tiempo_estado_inicial = t["T_PUNTO_INI_ANIM"] + t["T_PUNTO_INI_ESPERA"]
        tiempo_extra_iteracion_1 = (t["T_TANGENTE_INI_ANIM"] + t["T_TANGENTE_INI_ESPERA"]) if max_iteraciones >= 1 else 0.0
        
        t_hud = 4 * (t["T_HUD_ANIM"] + t["T_HUD_ESPERA"]) + t.get("T_HUD_SALIDA", 0.5)
        t_proy_punto = t["T_PROY_PUNTO_ANIM"] + t["T_PROY_PUNTO_ESPERA"]
        t_proy_linea = t["T_PROY_LINEA_ANIM"] + t["T_PROY_LINEA_ESPERA"]
        t_paralelo = t["T_TRANSICION_PARALELO_ANIM"] + t["T_TRANSICION_PARALELO_ESPERA"]
        t_limp_linea = t["T_LIMPIEZA_LINEA_ANIM"] + t["T_LIMPIEZA_LINEA_ESPERA"]
        t_limp_punto = t["T_LIMPIEZA_PUNTO_ANIM"] + t["T_LIMPIEZA_PUNTO_ESPERA"]
        
        tiempo_por_iteracion = t_hud + t_proy_punto + t_proy_linea + t_paralelo + t_limp_linea + t_limp_punto
        tiempo_iteraciones = (max_iteraciones * tiempo_por_iteracion) + tiempo_extra_iteracion_1

    elif metodo_norm == "serie_taylor":
        tiempo_estado_inicial = t["T_PUNTO_INI_ANIM"] + t["T_PUNTO_INI_ESPERA"]
        tiempo_extra_iteracion_1 = (t["T_TAYLOR_INI_ANIM"] + t["T_TAYLOR_INI_ESPERA"]) if max_iteraciones >= 1 else 0.0
        
        t_hud = t["T_HUD_ANIM"] + t["T_HUD_ESPERA"] + t.get("T_HUD_SALIDA", 0.3)
        t_transform = t["T_TAYLOR_TRANSFORM_ANIM"] + t["T_TAYLOR_TRANSFORM_ESPERA"]
        
        tiempo_por_iteracion = t_hud + t_transform
        tiempo_iteraciones = (max(0, max_iteraciones - 1) * tiempo_por_iteracion) + (t_hud + tiempo_extra_iteracion_1 if max_iteraciones >= 1 else 0.0)

    tiempo_total = tiempo_setup + tiempo_estado_inicial + tiempo_iteraciones + tiempo_cierre

    return {
        "metodo": metodo_norm,
        "max_iteraciones": max_iteraciones,
        "tiempo_total_maximo": round(tiempo_total, 2),
        "incluye_setup": incluir_setup,
        "tiempo_setup": round(tiempo_setup, 2),
        "tiempo_estado_inicial": round(tiempo_estado_inicial, 2),
        "tiempo_extra_iteracion_1": round(tiempo_extra_iteracion_1, 2),
        "tiempo_por_iteracion_recurrente": round(tiempo_por_iteracion, 2),
        "tiempo_iteraciones_total": round(tiempo_iteraciones, 2),
        "tiempo_cierre": round(tiempo_cierre, 2),
        "tiempos_utilizados": t
    }


def verificar_duracion_short(
    metodo: str,
    max_iteraciones: int,
    tiempos: Optional[Dict[str, Any]] = None,
    limite_segundos: float = 60.0,
    **kwargs
) -> Dict[str, Any]:
    """
    Verifica si una configuración de animación cabe dentro del límite de un Short (ej. 60s)
    e indica el margen de tiempo restante o el exceso.
    """
    desglose = desglosar_tiempo_maximo(
        metodo=metodo,
        max_iteraciones=max_iteraciones,
        tiempos=tiempos,
        **kwargs
    )
    total = desglose["tiempo_total_maximo"]
    cabe = total <= limite_segundos
    diferencia = round(limite_segundos - total, 2)

    return {
        **desglose,
        "limite_short_segundos": limite_segundos,
        "es_apto_short": cabe,
        "margen_restante": diferencia if cabe else 0.0,
        "tiempo_excedido": abs(diferencia) if not cabe else 0.0,
    }


# ==============================================================================
# 5. ESCALADO DE CADENCIA Y GENERACIÓN DE VECTOR DE TIEMPOS
# ==============================================================================

def calcular_vector_tiempos(
    metodo: str,
    max_iteraciones: int,
    tiempo_deseado: float = 60.0,
    incluir_setup: bool = True,
    escalar_setup: bool = True,
    redondear: int = 2
) -> Union[VectorTiempos, Dict[str, VectorTiempos]]:
    """
    Calcula y escala la cadencia de los tiempos de animación de modo que el método
    numérico especificado (con `max_iteraciones` iteraciones) encaje con exactitud
    dentro de `tiempo_deseado` segundos.

    Parámetros:
    -----------
    metodo : str
        Nombre del método: 'biseccion', 'regla_falsa', 'newton_raphson', o 'todos'.
        Si se pasa 'todos', retorna un diccionario con los vectores calculados para cada método.
    max_iteraciones : int
        Número de iteraciones deseadas que deben encajar en el tiempo objetivo.
    tiempo_deseado : float, opcional (por defecto 60.0)
        Duración objetivo en segundos que debe durar la animación completa (ej. 60s para Short).
    incluir_setup : bool, opcional (por defecto True)
        Si se incluye el tiempo de plano y gráfica inicial (4.5s) en el cálculo del total.
    escalar_setup : bool, opcional (por defecto True)
        - Si True: todos los tiempos (incluyendo setup) se escalan armónicamente.
        - Si False: el setup permanece fijo en 4.5s y solo se escalan las fases algorítmicas.
    redondear : int, opcional (por defecto 2)
        Número de decimales para redondear cada componente del vector de tiempos.

    Retorna:
    --------
    VectorTiempos (o Dict[str, VectorTiempos] si metodo='todos'):
        Vector con los tiempos calculados para cada paso del método numérico.
        Puede usarse como lista numérica ordinaria o accederse por nombre de clave.
    """
    if tiempo_deseado <= 0:
        raise ValueError("tiempo_deseado debe ser un número positivo mayor que 0.")

    metodo_norm = _normalizar_metodo(metodo)

    # Si se pide para todos los métodos, calcular iterativamente
    if metodo_norm == "todos":
        metodos_disponibles = ["biseccion", "regla_falsa", "newton_raphson", "serie_taylor"]
        resultado_todos: Dict[str, VectorTiempos] = {}
        for m in metodos_disponibles:
            resultado_todos[m] = calcular_vector_tiempos(
                metodo=m,
                max_iteraciones=max_iteraciones,
                tiempo_deseado=tiempo_deseado,
                incluir_setup=incluir_setup,
                escalar_setup=escalar_setup,
                redondear=redondear
            )
        return resultado_todos

    # 1. Obtener desglose base con los tiempos estándar predeterminados
    desglose_base = desglosar_tiempo_maximo(
        metodo=metodo_norm,
        max_iteraciones=max_iteraciones,
        incluir_setup=incluir_setup
    )
    t_base_total = desglose_base["tiempo_total_maximo"]
    t_setup_base = desglose_base["tiempo_setup"]
    tiempos_base = dict(desglose_base["tiempos_utilizados"])

    # 2. Calcular factor de escalado armónico
    if t_base_total <= 0:
        factor_escalado = 1.0
    elif not escalar_setup and incluir_setup:
        # El setup se mantiene fijo; se escala únicamente el remanente algorítmico
        tiempo_disp_algo = tiempo_deseado - t_setup_base
        tiempo_base_algo = t_base_total - t_setup_base
        if tiempo_disp_algo <= 0:
            raise ValueError(
                f"tiempo_deseado ({tiempo_deseado}s) es insuficiente para cubrir incluso el setup fijo ({t_setup_base}s)."
            )
        factor_escalado = tiempo_disp_algo / tiempo_base_algo if tiempo_base_algo > 0 else 1.0
    else:
        # Escalado global armónico de toda la animación
        factor_escalado = tiempo_deseado / t_base_total

    # 3. Aplicar factor a cada constante del método
    claves_ordenadas = obtener_claves_metodo(metodo_norm)
    tiempos_escalados: Dict[str, float] = {}

    for k in tiempos_base:
        es_clave_setup = k.startswith("T_SETUP_")
        if es_clave_setup and not escalar_setup:
            tiempos_escalados[k] = round(tiempos_base[k], redondear)
        else:
            val_escalado = tiempos_base[k] * factor_escalado
            tiempos_escalados[k] = round(val_escalado, redondear)

    # 4. Construir la lista / vector en el orden estándar de la plantilla
    valores_vector = [tiempos_escalados[k] for k in claves_ordenadas]

    # 5. Calcular tiempo total estimado con los valores redondeados
    t_estimado = calcular_tiempo_maximo(
        metodo=metodo_norm,
        max_iteraciones=max_iteraciones,
        tiempos=tiempos_escalados,
        incluir_setup=incluir_setup
    )

    return VectorTiempos(
        valores=valores_vector,
        claves=claves_ordenadas,
        metodo=metodo_norm,
        tiempo_objetivo=round(tiempo_deseado, redondear),
        tiempo_estimado=round(t_estimado, redondear),
        factor_escalado=round(factor_escalado, 4),
        tiempos_completos=tiempos_escalados
    )


# Alias semántico directo
escalar_cadencia = calcular_vector_tiempos


# ==============================================================================
# 6. DEMOSTRACIÓN Y PRUEBAS EN LÍNEA DE COMANDOS
# ==============================================================================

if __name__ == "__main__":
    print("=" * 75)
    print(" ESTIMACIÓN Y ESCALADO DE CADENCIA PARA SHORTS (tiempo.py)")
    print("=" * 75)

    TIEMPO_SHORT = 60.0  # 60 segundos objetivo
    ITERACIONES = 4

    print(f"\n[OBJETIVO] Ajustar cadencia para que {ITERACIONES} iteraciones duren exactamente ~{TIEMPO_SHORT}s:")
    
    vectores_todos = calcular_vector_tiempos(
        metodo="todos",
        max_iteraciones=ITERACIONES,
        tiempo_deseado=TIEMPO_SHORT,
        redondear=2
    )

    for metodo_nombre, vec in vectores_todos.items():
        print("-" * 75)
        print(f"MÉTODO: {metodo_nombre.upper()}")
        print(f"  * Factor de escalado : {vec.factor_escalado}x (aceleración: {round(1/vec.factor_escalado, 2)}x)")
        print(f"  * Tiempo estimado    : {vec.tiempo_estimado}s (Objetivo: {vec.tiempo_objetivo}s)")
        print(f"  * Vector de tiempos ({len(vec)} parámetros):")
        print(f"    {list(vec)}")
        print("\n  * Primeras constantes asignadas:")
        for clave, valor in list(vec.como_diccionario().items())[:6]:
            print(f"      {clave:25s} = {valor:.2f}s")

    print("\n" + "=" * 75)
    print(" EJEMPLO DE DESEMPAQUETADO RÁPIDO PARA BISECCIÓN:")
    print("=" * 75)
    v_bis = calcular_vector_tiempos("biseccion", max_iteraciones=4, tiempo_deseado=58.0)
    print(f"v_bis.T_HUD_ANIM           = {v_bis.T_HUD_ANIM}s")
    print(f"v_bis.T_MOVIMIENTO_CURVA_ANIM = {v_bis.T_MOVIMIENTO_CURVA_ANIM}s")
    print(f"Tiempo Total Resultante    = {v_bis.tiempo_estimado}s (Apto para YouTube Short: {v_bis.tiempo_estimado <= 60.0})")
