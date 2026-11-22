"""IR (representación intermedia) de una escena matemática.

El IR es la fuente de verdad del editor. El código Python se deriva de él y el
LLM solo puede proponer parches sobre esta estructura, nunca ejecutar código.
"""

from __future__ import annotations

import ast
import math
import re
from copy import deepcopy

SUPPORTED_METHODS = ("biseccion",)
FORMAT_IDS = ("16:9", "9:16", "1:1")
HUD_POSITIONS = ("UL", "UR", "DL", "DR")
BEAT_KINDS = ("setup", "interval", "iteration", "result", "close", "annotation")

_ALLOWED_FUNCS = {
    "sin", "cos", "tan", "asin", "acos", "atan",
    "sinh", "cosh", "tanh", "exp", "log", "log10",
    "sqrt", "abs", "pow", "floor", "ceil",
}
_ALLOWED_CONSTANTS = {"pi", "e", "tau"}
_ALLOWED_NAMES = {"x", "math"} | _ALLOWED_FUNCS | _ALLOWED_CONSTANTS

_ALLOWED_NODES = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Name,
    ast.Load, ast.Call, ast.Attribute,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod,
    ast.USub, ast.UAdd,
)

_HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


class IRValidationError(ValueError):
    """El IR no cumple el contrato de la escena."""


def _default_beats(max_iterations: int) -> list[dict]:
    beats = [
        {
            "id": "setup",
            "kind": "setup",
            "label": "Escribir f(x)",
            "t_anim": 1.0,
            "t_wait": 0.5,
            "enabled": True,
        },
        {
            "id": "interval",
            "kind": "interval",
            "label": "Marcar [a, b]",
            "t_anim": 0.8,
            "t_wait": 0.4,
            "enabled": True,
        },
    ]
    for index in range(1, max_iterations + 1):
        beats.append(
            {
                "id": f"iter_{index}",
                "kind": "iteration",
                "label": f"Iteración {index}",
                "t_anim": 1.2,
                "t_wait": 0.6,
                "enabled": True,
            }
        )
    beats.extend(
        [
            {
                "id": "result",
                "kind": "result",
                "label": "Resultado",
                "t_anim": 1.0,
                "t_wait": 2.0,
                "enabled": True,
            },
            {
                "id": "close",
                "kind": "close",
                "label": "Cierre",
                "t_anim": 1.5,
                "t_wait": 0.5,
                "enabled": True,
            },
        ]
    )
    return beats


def default_ir(method: str = "biseccion", **overrides) -> dict:
    if method not in SUPPORTED_METHODS:
        raise IRValidationError(f"Método no soportado: {method}")

    data = {
        "version": 1,
        "method": method,
        "title": "Bisección",
        "format": "16:9",
        "function": {
            "latex": r"f(x) = e^{x} - 3x^{2}",
            "python": "math.exp(x) - 3 * (x ** 2)",
            "domain": [-0.5, 2.0],
        },
        "params": {
            "a": 0.0,
            "b": 1.5,
            "tolerance": 0.0001,
            "max_iterations": 5,
        },
        "beats": _default_beats(5),
        "layout": {
            "hud": "UR",
            "show_grid": True,
            "accent": "#89b4fa",
            "result_color": "#a6e3a1",
        },
        "narration": {"audio": None, "offset": 0.0},
    }
    data.update(overrides)
    return normalize_ir(data)


def validate_expression(expression: str) -> str:
    """Valida una expresión Python de una variable `x`.

    Solo permite aritmética, nombres matemáticos de una lista blanca y
    `math.<funcion>`. Rechaza atributos, subíndices, lambdas y strings.
    """

    if not isinstance(expression, str):
        raise IRValidationError("La función debe ser una cadena.")
    expression = expression.strip()
    if not expression:
        raise IRValidationError("La función está vacía.")
    if len(expression) > 500:
        raise IRValidationError("La función es demasiado larga (máximo 500 caracteres).")

    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise IRValidationError(f"Sintaxis inválida en la función: {exc.msg}") from exc

    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise IRValidationError(
                f"Expresión no permitida: {type(node).__name__}. "
                "Usa solo x, números y funciones matemáticas."
            )

        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
                raise IRValidationError("Solo se permiten constantes numéricas.")
            if not math.isfinite(float(node.value)):
                raise IRValidationError("Las constantes deben ser finitas.")

        elif isinstance(node, ast.Name):
            if node.id not in _ALLOWED_NAMES:
                raise IRValidationError(f"Nombre no permitido: {node.id!r}.")

        elif isinstance(node, ast.Attribute):
            if not isinstance(node.value, ast.Name) or node.value.id != "math":
                raise IRValidationError("Solo se permite el prefijo math.<funcion>.")
            if node.attr not in _ALLOWED_FUNCS | _ALLOWED_CONSTANTS:
                raise IRValidationError(f"Función math no permitida: {node.attr!r}.")

        elif isinstance(node, ast.Call):
            if node.keywords:
                raise IRValidationError("Las funciones no aceptan argumentos con nombre.")
            if any(isinstance(arg, ast.Starred) for arg in node.args):
                raise IRValidationError("No se permiten argumentos expandidos.")
            if isinstance(node.func, ast.Name):
                if node.func.id not in _ALLOWED_FUNCS:
                    raise IRValidationError(f"Función no permitida: {node.func.id!r}.")
            elif isinstance(node.func, ast.Attribute):
                if node.func.attr not in _ALLOWED_FUNCS:
                    raise IRValidationError(f"Función math no permitida: {node.func.attr!r}.")
            else:
                raise IRValidationError("Llamada a función no permitida.")

    return expression


def compile_expression(expression: str):
    validate_expression(expression)
    return compile(expression, "<scene-function>", "eval")


_BUILTIN_FUNCS = {"abs": abs, "pow": pow}


def math_namespace() -> dict:
    """Nombres matemáticos permitidos por la lista blanca.

    `abs` y `pow` viven en builtins, no en `math`; se resuelven aparte.
    """

    namespace: dict = {"math": math}
    for name in _ALLOWED_FUNCS:
        namespace[name] = _BUILTIN_FUNCS.get(name) or getattr(math, name)
    for name in _ALLOWED_CONSTANTS:
        namespace[name] = getattr(math, name)
    return namespace


def evaluate_expression(expression: str, x_value: float) -> float:
    code = compile_expression(expression)
    namespace = {"__builtins__": {}, **math_namespace()}
    namespace["x"] = float(x_value)
    value = eval(code, namespace)  # noqa: S307 - AST ya validado
    if isinstance(value, complex) or not math.isfinite(float(value)):
        raise IRValidationError(f"f({x_value:g}) no es un número real finito.")
    return float(value)


def _as_float(value, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise IRValidationError(f"{name} debe ser numérico.") from exc
    if not math.isfinite(number):
        raise IRValidationError(f"{name} debe ser finito.")
    return number


def _normalize_function(function: dict) -> dict:
    if not isinstance(function, dict):
        raise IRValidationError("`function` debe ser un objeto.")

    python_expr = validate_expression(function.get("python", ""))
    latex = function.get("latex", "")
    if not isinstance(latex, str) or not latex.strip():
        raise IRValidationError("`function.latex` es obligatorio.")
    if len(latex) > 500:
        raise IRValidationError("`function.latex` es demasiado largo.")

    domain = function.get("domain", [-5.0, 5.0])
    if not isinstance(domain, (list, tuple)) or len(domain) != 2:
        raise IRValidationError("`function.domain` debe ser [x_min, x_max].")
    x_min = _as_float(domain[0], "function.domain[0]")
    x_max = _as_float(domain[1], "function.domain[1]")
    if x_min >= x_max:
        raise IRValidationError("El dominio debe cumplir x_min < x_max.")

    return {
        "latex": latex.strip(),
        "python": python_expr,
        "domain": [x_min, x_max],
    }


def _normalize_params(params: dict, domain: list[float]) -> dict:
    if not isinstance(params, dict):
        raise IRValidationError("`params` debe ser un objeto.")

    a = _as_float(params.get("a", domain[0]), "params.a")
    b = _as_float(params.get("b", domain[1]), "params.b")
    tolerance = _as_float(params.get("tolerance", 0.0001), "params.tolerance")
    try:
        max_iterations = int(params.get("max_iterations", 5))
    except (TypeError, ValueError) as exc:
        raise IRValidationError("max_iterations debe ser un entero.") from exc

    if a >= b:
        raise IRValidationError("Los extremos deben cumplir a < b.")
    if tolerance <= 0:
        raise IRValidationError("La tolerancia debe ser mayor que 0.")
    if not 1 <= max_iterations <= 20:
        raise IRValidationError("max_iterations debe estar entre 1 y 20.")

    margin = 1e-9
    if a < domain[0] - margin or b > domain[1] + margin:
        raise IRValidationError(
            f"El intervalo [{a:g}, {b:g}] debe estar dentro del dominio "
            f"[{domain[0]:g}, {domain[1]:g}]."
        )

    return {
        "a": a,
        "b": b,
        "tolerance": tolerance,
        "max_iterations": max_iterations,
    }


def _normalize_beats(beats, max_iterations: int) -> list[dict]:
    if not isinstance(beats, list) or not beats:
        return _default_beats(max_iterations)

    normalized: list[dict] = []
    seen_ids: set[str] = set()

    for index, beat in enumerate(beats):
        if not isinstance(beat, dict):
            raise IRValidationError(f"El beat {index} debe ser un objeto.")
        beat_id = str(beat.get("id") or f"beat_{index}")
        if beat_id in seen_ids:
            raise IRValidationError(f"Id de beat duplicado: {beat_id!r}.")
        seen_ids.add(beat_id)

        kind = str(beat.get("kind", "annotation"))
        if kind not in BEAT_KINDS:
            raise IRValidationError(f"Tipo de beat no válido: {kind!r}.")

        t_anim = _as_float(beat.get("t_anim", 1.0), f"beats[{index}].t_anim")
        t_wait = _as_float(beat.get("t_wait", 0.5), f"beats[{index}].t_wait")
        if not 0.1 <= t_anim <= 10.0:
            raise IRValidationError("t_anim debe estar entre 0.1 y 10 segundos.")
        if not 0.0 <= t_wait <= 10.0:
            raise IRValidationError("t_wait debe estar entre 0 y 10 segundos.")

        normalized.append(
            {
                "id": beat_id,
                "kind": kind,
                "label": str(beat.get("label", beat_id))[:120],
                "t_anim": t_anim,
                "t_wait": t_wait,
                "enabled": bool(beat.get("enabled", True)),
            }
        )

    # Sincroniza los beats de iteración con max_iterations conservando tiempos.
    iteration_beats = [b for b in normalized if b["kind"] == "iteration"]
    for index in range(len(iteration_beats) + 1, max_iterations + 1):
        normalized.append(
            {
                "id": f"iter_{index}",
                "kind": "iteration",
                "label": f"Iteración {index}",
                "t_anim": 1.2,
                "t_wait": 0.6,
                "enabled": True,
            }
        )
    if len(iteration_beats) > max_iterations:
        keep = {b["id"] for b in iteration_beats[:max_iterations]}
        normalized = [
            b for b in normalized
            if b["kind"] != "iteration" or b["id"] in keep
        ]

    return normalized


def _normalize_layout(layout: dict) -> dict:
    if not isinstance(layout, dict):
        layout = {}

    hud = str(layout.get("hud", "UR")).upper()
    if hud not in HUD_POSITIONS:
        raise IRValidationError("layout.hud debe ser UL, UR, DL o DR.")

    accent = str(layout.get("accent", "#89b4fa"))
    result_color = str(layout.get("result_color", "#a6e3a1"))
    for name, color in (("accent", accent), ("result_color", result_color)):
        if not _HEX_COLOR.match(color):
            raise IRValidationError(f"layout.{name} debe ser un color #RRGGBB.")

    return {
        "hud": hud,
        "show_grid": bool(layout.get("show_grid", True)),
        "accent": accent,
        "result_color": result_color,
    }


def _normalize_narration(narration: dict) -> dict:
    if not isinstance(narration, dict):
        narration = {}

    audio = narration.get("audio")
    if audio is not None:
        audio = str(audio)
        if "/" in audio or "\\" in audio or ".." in audio:
            raise IRValidationError("narration.audio debe ser un nombre de archivo simple.")

    return {
        "audio": audio,
        "offset": _as_float(narration.get("offset", 0.0), "narration.offset"),
    }


def normalize_ir(data: dict, *, check_math: bool = True) -> dict:
    """Valida y normaliza un IR completo."""

    if not isinstance(data, dict):
        raise IRValidationError("El IR debe ser un objeto JSON.")

    method = str(data.get("method", "biseccion"))
    if method not in SUPPORTED_METHODS:
        raise IRValidationError(f"Método no soportado: {method!r}.")

    title = str(data.get("title", "Escena"))[:120].strip() or "Escena"

    format_id = str(data.get("format", "16:9"))
    if format_id not in FORMAT_IDS:
        raise IRValidationError(f"Formato no soportado: {format_id!r}.")

    function = _normalize_function(data.get("function", {}))
    params = _normalize_params(data.get("params", {}), function["domain"])

    if check_math:
        fa = evaluate_expression(function["python"], params["a"])
        fb = evaluate_expression(function["python"], params["b"])
        if fa * fb > 0:
            raise IRValidationError(
                "f(a) y f(b) tienen el mismo signo: el método no puede bracketear "
                "una raíz en ese intervalo."
            )

    return {
        "version": 1,
        "method": method,
        "title": title,
        "format": format_id,
        "function": function,
        "params": params,
        "beats": _normalize_beats(data.get("beats"), params["max_iterations"]),
        "layout": _normalize_layout(data.get("layout", {})),
        "narration": _normalize_narration(data.get("narration", {})),
    }


def merge_patch(current: dict, patch: dict) -> dict:
    """Aplica un parche superficial/por subobjeto y vuelve a validar.

    Los parches del LLM no pueden añadir claves fuera del contrato del IR.
    """

    if not isinstance(patch, dict):
        raise IRValidationError("El parche debe ser un objeto JSON.")

    allowed = {"title", "format", "function", "params", "beats", "layout", "narration"}
    unknown = set(patch) - allowed
    if unknown:
        raise IRValidationError(f"Claves no permitidas en el parche: {sorted(unknown)}")

    merged = deepcopy(current)
    for key, value in patch.items():
        if key in {"function", "params", "layout", "narration"}:
            if not isinstance(value, dict):
                raise IRValidationError(f"`{key}` debe ser un objeto.")
            merged[key] = {**merged.get(key, {}), **value}
        else:
            merged[key] = deepcopy(value)

    return normalize_ir(merged)


def beat_times(ir: dict, kind: str, index: int | None = None) -> tuple[float, float]:
    """Devuelve (t_anim, t_wait) del beat solicitado o un fallback estable."""

    candidates = [b for b in ir.get("beats", []) if b.get("kind") == kind and b.get("enabled", True)]
    if index is not None:
        expected_id = f"iter_{index}" if kind == "iteration" else f"{kind}_{index}"
        candidates = [b for b in candidates if b.get("id") == expected_id]
    if candidates:
        beat = candidates[0]
        return float(beat["t_anim"]), float(beat["t_wait"])

    defaults = {
        "setup": (1.0, 0.5),
        "interval": (0.8, 0.4),
        "iteration": (1.2, 0.6),
        "result": (1.0, 2.0),
        "close": (1.5, 0.5),
        "annotation": (0.8, 0.4),
    }
    return defaults.get(kind, (1.0, 0.5))
