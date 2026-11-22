"""Runtime de la escena de bisección.

Recibe el IR, calcula las iteraciones y encola las acciones en
`AnimadorGrafico`. No conoce HTTP ni la base de datos.
"""

from __future__ import annotations

import math
import os

from manim import DOWN, GREEN, GREY_B, YELLOW

from app.ir import beat_times, compile_expression, math_namespace
from Planos.generar_plano import AnimadorGrafico


def _make_function(expression: str):
    code = compile_expression(expression)
    namespace = {"__builtins__": {}, **math_namespace()}
    namespace["x"] = 0.0

    def f(x_value: float) -> float:
        namespace["x"] = float(x_value)
        try:
            return float(eval(code, namespace))  # noqa: S307 - AST validado en el IR
        except (OverflowError, ValueError, ZeroDivisionError):
            return float("nan")

    return f


def _bisect(f, a: float, b: float, tolerance: float, max_iterations: int):
    fa, fb = f(a), f(b)
    if not (math.isfinite(fa) and math.isfinite(fb)):
        raise ValueError("La función no es finita en los extremos del intervalo.")
    if fa * fb > 0:
        raise ValueError(
            "f(a) y f(b) tienen el mismo signo: la bisección no puede bracketear una raíz."
        )

    rows = []
    midpoint = (a + b) / 2.0
    for index in range(1, max_iterations + 1):
        midpoint = (a + b) / 2.0
        f_mid = f(midpoint)
        if not math.isfinite(f_mid):
            raise ValueError(f"f({midpoint:g}) no es un número real finito.")

        rows.append(
            {
                "iteration": index,
                "a": a,
                "b": b,
                "c": midpoint,
                "f_c": f_mid,
                "error": abs(b - a) / 2.0,
            }
        )

        if abs(f_mid) <= 1e-12 or abs(b - a) / 2.0 <= tolerance:
            break

        if fa * f_mid < 0:
            b, fb = midpoint, f_mid
        else:
            a, fa = midpoint, f_mid

    return rows, midpoint


def _iteration_latex(row: dict) -> str:
    return (
        rf"c_{{{row['iteration']}}} = {row['c']:.4f}"
        rf"\quad f(c_{{{row['iteration']}}}) = {row['f_c']:.4f}"
    )


def construir_biseccion(ir: dict) -> None:
    """Construye y renderiza la escena descrita por el IR."""

    function = ir["function"]
    params = ir["params"]
    layout = ir.get("layout", {})
    format_id = ir.get("format", "16:9")
    quality = os.environ.get("MANIM_QUALITY", "low_quality")
    media_dir = os.environ.get("MANIM_MEDIA_DIR")

    f = _make_function(function["python"])
    rows, root = _bisect(
        f,
        params["a"],
        params["b"],
        params["tolerance"],
        params["max_iterations"],
    )

    x_min, x_max = function["domain"]
    escena = AnimadorGrafico(f, x_min=x_min, x_max=x_max)

    # 1. Enunciado de la función.
    t_anim, t_wait = beat_times(ir, "setup")
    escena.agregar_algebra_flotante(
        function["latex"],
        posicion=layout.get("hud", "UR"),
        id="hud_fn",
        remover_al_final=False,
        tiempo_animacion=t_anim,
        tiempo_espera=t_wait,
    )

    # 2. Intervalo inicial.
    t_anim, t_wait = beat_times(ir, "interval")
    escena.agregar_punto(
        params["a"], f(params["a"]),
        color=YELLOW, label=True, id="punto_a",
        tiempo_animacion=t_anim, tiempo_espera=t_wait,
    )
    escena.agregar_punto(
        params["b"], f(params["b"]),
        color=YELLOW, label=True, id="punto_b",
        tiempo_animacion=t_anim, tiempo_espera=t_wait,
    )

    # 3. Iteraciones.
    hud_created = False
    for row in rows:
        index = row["iteration"]
        t_anim, t_wait = beat_times(ir, "iteration", index)
        t_line = max(0.2, t_anim * 0.4)

        escena.agregar_punto(
            row["c"], row["f_c"],
            color="#00FFCC", label=True, id=f"punto_c_{index}",
            tiempo_animacion=t_anim, tiempo_espera=0.0,
        )
        escena.animar_linea_punteada(
            row["c"], row["c"], row["c"], row["c"],
            0.0, row["f_c"], 0.0, row["f_c"],
            color=GREY_B,
            tiempo_animacion=t_line,
            tiempo_espera=0.0,
            id=f"linea_c_{index}",
        )

        latex = _iteration_latex(row)
        if hud_created:
            escena.transformar_algebra_flotante(
                "hud_iter",
                latex,
                posicion="DR",
                tiempo_animacion=t_anim,
                tiempo_espera=t_wait,
            )
        else:
            escena.agregar_algebra_flotante(
                latex,
                posicion="DR",
                id="hud_iter",
                remover_al_final=False,
                tiempo_animacion=t_anim,
                tiempo_espera=t_wait,
            )
            hud_created = True

        # La guía vertical ya cumplió su función; se retira en la siguiente.
        if index > 1:
            escena.eliminar_objeto(
                id=f"linea_c_{index - 1}",
                animacion="FadeOut",
                tiempo_animacion=0.2,
                tiempo_espera=0.0,
            )

    # 4. Resultado.
    t_anim, t_wait = beat_times(ir, "result")
    escena.agregar_punto(
        root, f(root),
        color=layout.get("result_color", GREEN),
        label=True,
        id="punto_raiz",
        tiempo_animacion=t_anim,
        tiempo_espera=0.0,
    )
    resultado = rf"x^* \approx {root:.6f}"
    if hud_created:
        escena.transformar_algebra_flotante(
            "hud_iter",
            resultado,
            posicion="DR",
            tiempo_animacion=t_anim,
            tiempo_espera=t_wait,
        )
    else:
        escena.agregar_algebra_flotante(
            resultado,
            posicion="DR",
            id="hud_iter",
            tiempo_animacion=t_anim,
            tiempo_espera=t_wait,
        )

    # 5. Cierre.
    t_anim, t_wait = beat_times(ir, "close")
    escena.desvanecer_todo(
        animacion="FadeOut",
        tiempo_animacion=t_anim,
        tiempo_espera=t_wait,
    )

    escena.render(
        previsualizar=False,
        calidad=quality,
        formato=format_id,
        media_dir=media_dir,
    )
