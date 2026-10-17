"""
================================================================================
MÓDULO: generador_short.py (Plantillas/Short)
Generador automatizado de animaciones matemáticas para Shorts (9:16 / 16:9)
utilizando directamente los scripts de las carpetas de Plantillas
(Análisis numérico y Cálculo diferencial) y sustituyendo las variables
por las ingresadas por el usuario.
================================================================================
"""

import os
import sys
import re
import math
from typing import Dict, Any, Optional

try:
    from Plantillas.Short.tiempo import (
        calcular_vector_tiempos,
        desglosar_tiempo_maximo,
        verificar_duracion_short,
        VectorTiempos
    )
except ImportError:
    try:
        from tiempo import (
            calcular_vector_tiempos,
            desglosar_tiempo_maximo,
            verificar_duracion_short,
            VectorTiempos
        )
    except ImportError:
        directorio_actual = os.path.dirname(os.path.abspath(__file__))
        if directorio_actual not in sys.path:
            sys.path.insert(0, directorio_actual)
        from tiempo import (
            calcular_vector_tiempos,
            desglosar_tiempo_maximo,
            verificar_duracion_short,
            VectorTiempos
        )

# Soporte simbólico con SymPy para derivación analítica y generación de LaTeX
try:
    import sympy
    HAY_SYMPY = True
except ImportError:
    HAY_SYMPY = False

# Directorio raíz del proyecto y directorio de plantillas
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PLANTILLAS_DIR = os.path.join(BASE_DIR, "Plantillas")

# Mapeo de métodos soportados a sus scripts originales en las carpetas de Plantillas
METODO_ARCHIVOS = {
    "biseccion": os.path.join(PLANTILLAS_DIR, "Análisis numérico", "Bisección.py"),
    "regla_falsa": os.path.join(PLANTILLAS_DIR, "Análisis numérico", "Regla falsa.py"),
    "newton_raphson": os.path.join(PLANTILLAS_DIR, "Análisis numérico", "Newton-Raphson.py"),
    "serie_taylor": os.path.join(PLANTILLAS_DIR, "Cálculo diferencial", "Serie de Taylor.py"),
    "integral": os.path.join(PLANTILLAS_DIR, "Cálculo diferencial", "Integral.py"),
    "derivada_limite": os.path.join(PLANTILLAS_DIR, "Cálculo diferencial", "Derivada límite.py"),
}


def normalizar_expresion_matematica(expr_str: str) -> str:
    """
    Limpia y normaliza una expresión matemática introducida por el usuario
    para que sea compatible con Python / SymPy.
    """
    s = expr_str.strip()
    if not s:
        return "exp(x) - 3*(x**2)"

    # Reemplazo de funciones comunes en español
    s = re.sub(r'\bsen\(', 'sin(', s)
    s = re.sub(r'\btg\(', 'tan(', s)
    s = re.sub(r'\bln\(', 'log(', s)

    # Reemplazo de potencias ^ por **
    s = s.replace('^', '**')

    # Reemplazo de e** o e^ por exp
    s = re.sub(r'\be\*\*\(', 'exp(', s)
    s = re.sub(r'\be\*\*([a-zA-Z0-9_]+)', r'exp(\1)', s)

    # Multiplicación implícita básica: ej. 3x -> 3*x, 3( -> 3*(
    s = re.sub(r'(\d+)\s*([a-zA-Z])', r'\1*\2', s)
    s = re.sub(r'(\d+)\s*\(', r'\1*(', s)
    s = re.sub(r'\)\s*\(', r')*(', s)

    return s


def procesar_funcion_simbolica(expr_str: str) -> Dict[str, Any]:
    """
    Analiza una expresión matemática en variable x, calcula su derivada analítica
    y genera su código Python ejecutable y su representación en LaTeX.
    """
    expr_limpia = normalizar_expresion_matematica(expr_str)

    if HAY_SYMPY:
        try:
            x = sympy.Symbol('x')
            expr_sympy = sympy.sympify(expr_limpia, locals={'e': sympy.E})
            deriv_sympy = sympy.diff(expr_sympy, x)

            # Código python puro usando math
            py_func = sympy.pycode(expr_sympy)
            py_deriv = sympy.pycode(deriv_sympy)

            # Asegurar prefijo math. si sympy genera funciones estándar
            for fn in ['exp', 'sin', 'cos', 'tan', 'log', 'sqrt']:
                py_func = re.sub(rf'(?<!math\.)\b{fn}\(', f'math.{fn}(', py_func)
                py_deriv = re.sub(rf'(?<!math\.)\b{fn}\(', f'math.{fn}(', py_deriv)

            latex_func = sympy.latex(expr_sympy)
            latex_deriv = sympy.latex(deriv_sympy)

            return {
                "expr_original": expr_str,
                "expr_procesada": expr_limpia,
                "py_func_body": f"return {py_func}",
                "py_deriv_body": f"return {py_deriv}",
                "latex_func": f"f(x) = {latex_func}",
                "latex_deriv": f"f'(x) = {latex_deriv}",
                "simbolico": True
            }
        except Exception:
            pass

    # Fallback sin sympy o si falla sympify
    py_func = expr_limpia
    for fn in ['exp', 'sin', 'cos', 'tan', 'log', 'sqrt']:
        py_func = re.sub(rf'(?<!math\.)\b{fn}\(', f'math.{fn}(', py_func)

    return {
        "expr_original": expr_str,
        "expr_procesada": expr_limpia,
        "py_func_body": f"return {py_func}",
        "py_deriv_body": "h = 1e-6\n    return (f_objetivo(x + h) - f_objetivo(x - h)) / (2 * h)",
        "latex_func": f"f(x) = {expr_str}",
        "latex_deriv": "f'(x) \\approx \\frac{f(x+h)-f(x-h)}{2h}",
        "simbolico": False
    }


def calcular_escala_tiempo(metodo: str, tiempo_deseado: float, max_iteraciones: int) -> float:
    """
    Calcula el multiplicador de velocidad para la variable 'ESCALA_TIEMPO' en cada script,
    donde 1.0 es la velocidad estándar base calibrada en las plantillas.
    """
    m = metodo.strip().lower().replace("-", "_").replace(" ", "_")
    n = max(1, int(max_iteraciones))

    # Tiempos base nominales (en segundos) a ESCALA_TIEMPO = 1.0
    if "bisecc" in m:
        t_base = 5.4 + 4.4 * n
    elif "regla" in m or "falsa" in m:
        t_base = 6.2 + 4.4 * n
    elif "newton" in m or "raphson" in m:
        t_base = 7.1 + 4.4 * n
    elif "taylor" in m or "serie" in m:
        t_base = 5.0 + 3.0 * n
    elif "integral" in m:
        t_base = 9.8 + 4.1 * n
    elif "derivada" in m:
        t_base = 21.0
    else:
        t_base = 5.4 + 4.4 * n

    escala = float(tiempo_deseado) / max(0.1, t_base)
    return round(max(0.1, min(5.0, escala)), 3)


def generar_codigo_short(
    metodo: str,
    funcion: str = "exp(x) - 3*(x**2)",
    tiempo_deseado: float = 60.0,
    max_iteraciones: int = 4,
    a: float = 0.0,
    b: float = 1.5,
    x0: float = 1.5,
    x_min: float = -0.5,
    x_max: float = 2.0,
    tolerancia: float = 0.0001,
    save_to_main: bool = False,
    ruta_main: Optional[str] = None
) -> Dict[str, Any]:
    """
    Función principal para generar el código ejecutable de un Short de Manim.
    Lee directamente el archivo original de la plantilla correspondiente desde la
    carpeta 'Plantillas/' y sustituye las variables por las configuradas por el usuario.
    """
    metodo_norm = metodo.strip().lower().replace("-", "_").replace(" ", "_")
    if "bisecc" in metodo_norm:
        metodo_clave = "biseccion"
    elif "regla" in metodo_norm or "falsa" in metodo_norm:
        metodo_clave = "regla_falsa"
    elif "newton" in metodo_norm or "raphson" in metodo_norm:
        metodo_clave = "newton_raphson"
    elif "taylor" in metodo_norm or "serie" in metodo_norm:
        metodo_clave = "serie_taylor"
    elif "integral" in metodo_norm:
        metodo_clave = "integral"
    elif "derivada" in metodo_norm or "limite" in metodo_norm:
        metodo_clave = "derivada_limite"
    else:
        metodo_clave = "biseccion"

    # 1. Localizar y leer directamente el script de la plantilla
    ruta_plantilla = METODO_ARCHIVOS.get(metodo_clave)
    if not ruta_plantilla or not os.path.isfile(ruta_plantilla):
        raise FileNotFoundError(
            f"No se encontró el script de plantilla para '{metodo_clave}' en: {ruta_plantilla}"
        )

    with open(ruta_plantilla, "r", encoding="utf-8") as f:
        codigo = f.read()

    # 2. Calcular vector de cadencia temporal escalado para el Short
    metodo_tiempo = metodo_clave if metodo_clave in ["biseccion", "regla_falsa", "newton_raphson", "serie_taylor"] else "biseccion"
    vector = calcular_vector_tiempos(
        metodo=metodo_tiempo,
        max_iteraciones=max_iteraciones,
        tiempo_deseado=tiempo_deseado,
        incluir_setup=True,
        escalar_setup=True,
        redondear=3
    )

    # 3. Sustitución de variables según el método
    if metodo_clave == "serie_taylor":
        expr_limpia = normalizar_expresion_matematica(funcion)
        info_fn = {
            "expr_original": funcion,
            "expr_procesada": expr_limpia,
            "latex_func": f"f(x) = {expr_limpia}",
            "simbolico": True
        }

        # Sustituir f_expr simbólica
        codigo = re.sub(
            r'f_expr\s*=\s*[^\n]+',
            f"f_expr = sp.sympify('{expr_limpia}', locals={{'e': sp.E}})",
            codigo
        )
        # Centro de expansión A_EXPANSION
        codigo = re.sub(
            r'\bA_EXPANSION\s*=\s*[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?',
            f"A_EXPANSION = {float(x0)}",
            codigo
        )
        # Grado o número de términos
        codigo = re.sub(
            r'\b(?:NUM_TERMINOS|MAX_GRADO)\s*=\s*\d+',
            f"NUM_TERMINOS = {int(max_iteraciones)}",
            codigo
        )
        # Dominio cartesiano
        codigo = re.sub(
            r'x_min\s*=\s*[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?',
            f"x_min={float(x_min)}",
            codigo
        )
        codigo = re.sub(
            r'x_max\s*=\s*[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?',
            f"x_max={float(x_max)}",
            codigo
        )

    else:
        # Métodos numéricos: Bisección, Regla Falsa, Newton-Raphson, Derivada, Integral
        info_fn = procesar_funcion_simbolica(funcion)

        # 3.1. Sustituir cuerpo de f_objetivo
        codigo = re.sub(
            r'(def\s+f_objetivo\s*\([^)]*\)\s*(?:->\s*[^:]+)?:\s*(?:"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\')?\s*)\n\s+return\s+[^\n]+',
            rf"\1\n    {info_fn['py_func_body']}",
            codigo
        )

        # 3.2. Sustituir derivada exacta si el método lo incluye (Newton-Raphson)
        if metodo_clave == "newton_raphson":
            codigo = re.sub(
                r'(def\s+f_derivada\s*\([^)]*\)\s*(?:->\s*[^:]+)?:\s*(?:"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\')?\s*)\n\s+return\s+[^\n]+',
                rf"\1\n    {info_fn['py_deriv_body']}",
                codigo
            )

        # 3.3. Sustituir LABEL_FUNCION
        latex_label = info_fn.get("latex_func", "f(x)")
        codigo = re.sub(
            r'LABEL_FUNCION\s*=\s*[^\n]+',
            lambda m: f'LABEL_FUNCION = r"$${latex_label}$$"',
            codigo
        )

        # 3.4. Sustituir variables de intervalo y semilla
        codigo = re.sub(
            r'\bA_INICIAL\s*=\s*[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?',
            f"A_INICIAL = {float(a)}",
            codigo
        )
        codigo = re.sub(
            r'\bB_INICIAL\s*=\s*[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?',
            f"B_INICIAL = {float(b)}",
            codigo
        )
        codigo = re.sub(
            r'\bX_INICIAL\s*=\s*[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?',
            f"X_INICIAL = {float(x0)}",
            codigo
        )

        # 3.5. Sustituir tolerancia e iteraciones
        codigo = re.sub(
            r'\bTOLERANCIA\s*=\s*[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?',
            f"TOLERANCIA = {float(tolerancia)}",
            codigo
        )
        codigo = re.sub(
            r'\bMAX_ITERACIONES\s*=\s*\d+',
            f"MAX_ITERACIONES = {int(max_iteraciones)}",
            codigo
        )

        # 3.6. Sustituir dominio del plano
        codigo = re.sub(
            r'x_min\s*=\s*[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?',
            f"x_min={float(x_min)}",
            codigo
        )
        codigo = re.sub(
            r'x_max\s*=\s*[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?',
            f"x_max={float(x_max)}",
            codigo
        )

        # 3.8. Sustituir constantes T_ directas si la plantilla las define individualmente
        mapa_tiempos = vector.to_dict()
        for k, v in mapa_tiempos.items():
            codigo = re.sub(
                rf'\b{k}\s*=\s*[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?',
                f"{k} = {v}",
                codigo
            )

    # 3.9. Conectar tiempo objetivo con la variable ESCALA_TIEMPO para todos los métodos
    escala_tiempo = calcular_escala_tiempo(metodo_clave, tiempo_deseado, max_iteraciones)
    if re.search(r'\bESCALA_TIEMPO\s*=', codigo):
        codigo = re.sub(
            r'\bESCALA_TIEMPO\s*=\s*[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?',
            f"ESCALA_TIEMPO = {escala_tiempo}",
            codigo
        )

    # 4. Guardar opcionalmente en el archivo principal (main.py)
    guardado = False
    if save_to_main:
        if not ruta_main:
            ruta_main = os.path.join(BASE_DIR, "main.py")
        try:
            with open(ruta_main, "w", encoding="utf-8") as f:
                f.write(codigo)
            guardado = True
        except Exception:
            guardado = False

    desglose = desglosar_tiempo_maximo(
        metodo=metodo_tiempo,
        max_iteraciones=max_iteraciones,
        tiempos=vector.to_dict()
    )

    return {
        "status": "success",
        "metodo": metodo_clave,
        "codigo": codigo,
        "archivo_plantilla_origen": ruta_plantilla,
        "vector_tiempos": list(vector),
        "mapa_tiempos": vector.to_dict(),
        "claves_tiempos": vector.claves,
        "factor_escalado": vector.factor_escalado,
        "tiempo_estimado": vector.tiempo_estimado,
        "tiempo_objetivo": vector.tiempo_objetivo,
        "escala_tiempo": escala_tiempo,
        "es_apto_short": vector.tiempo_estimado <= 60.0,
        "info_funcion": info_fn,
        "desglose": desglose,
        "guardado_en_main": guardado
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generador de Shorts Manim")
    parser.add_argument("--metodo", default="biseccion", choices=["biseccion", "regla_falsa", "newton_raphson", "serie_taylor"])
    parser.add_argument("--funcion", default="exp(x) - 3*(x**2)")
    parser.add_argument("--tiempo", type=float, default=60.0)
    parser.add_argument("--iteraciones", type=int, default=4)
    parser.add_argument("--save-main", action="store_true")

    args = parser.parse_args()
    res = generar_codigo_short(
        metodo=args.metodo,
        funcion=args.funcion,
        tiempo_deseado=args.tiempo,
        max_iteraciones=args.iteraciones,
        save_to_main=args.save_main
    )

    print("==================================================")
    print(f"Short generado: {res['metodo']} desde {res['archivo_plantilla_origen']}")
    print(f"Objetivo: {res['tiempo_objetivo']}s | Estimado: {res['tiempo_estimado']}s | Factor: {res['factor_escalado']}x")
    print(f"Función LaTeX: {res['info_funcion']['latex_func']}")
    print("==================================================")
    print(res['codigo'][:400] + "\n... [continúa]")
