"""Prompts del asistente de escenas.

El modelo nunca escribe Python: propone un parche sobre el IR y el servidor lo
valida antes de aplicarlo. El prompt está redactado en español para que la
respuesta también lo esté.
"""

from __future__ import annotations

import json
from typing import Any

SUMMARY_LABELS = {
    "title": "título",
    "format": "formato",
    "function": "función",
    "params": "parámetros",
    "beats": "ritmo",
    "layout": "estilo",
    "narration": "audio",
}

SYSTEM_PROMPT = """Eres el asistente de un editor de animaciones matemáticas con Manim.

La fuente de verdad es el IR de la escena. NUNCA devuelvas código Python.
Responde ÚNICAMENTE un objeto JSON con esta forma exacta:
{"reply": "...", "summary": ["ritmo", "formato"], "patch": {...}}

Reglas:
- `reply`: español, máximo dos frases, sin mencionar JSON ni implementación.
- `summary`: lista corta de etiquetas entre: título, formato, función, parámetros, ritmo, estilo, audio.
- `patch`: solo las claves del IR que el usuario pidió cambiar. Las permitidas son:
  title, format, function, params, beats, layout, narration.
- No cambies campos que el usuario no pidió. Si solo pide acelerar, cambia únicamente `beats`.
- `format` solo puede ser "16:9", "9:16" o "1:1".
- `function` tiene `latex` (válido para KaTeX), `python` (expresión de una variable x
  usando solo números, x, math.* y funciones como sin/cos/exp/log/sqrt/abs/pow) y
  `domain` = [x_min, x_max] con x_min < x_max.
- `params` tiene `a`, `b`, `tolerance` (> 0), `max_iterations` (entero de 1 a 20).
  Debe cumplirse siempre f(a) * f(b) <= 0 y a, b dentro de function.domain.
- `beats` es una lista de objetos con id, kind (setup, interval, iteration, result,
  close, annotation), label, t_anim (0.1 a 10), t_wait (0 a 10) y enabled (booleano).
- `layout` tiene hud (UL, UR, DL o DR), show_grid, accent y result_color (colors #RRGGBB).
- `narration` tiene audio (nombre de archivo simple o null) y offset (número).
- Si la petición es ambigua, imposible o rompería f(a) * f(b) <= 0, devuelve
  {"reply": "Pregunta corta aclaratoria.", "summary": [], "patch": {}}.
- No incluyas comentarios ni texto fuera del JSON.
"""


CODE_SYSTEM_PROMPT = """Eres el asistente de código de Manim Studio. El usuario trabaja sobre un archivo Python.

Responde ÚNICAMENTE un objeto JSON con esta forma exacta:
{"reply": "...", "summary": ["formato"], "code": "archivo Python completo"}

Reglas:
- `code` debe ser el archivo COMPLETO, con único cambio solicitado y sintaxis Python válida.
- No cambies comentarios, nombres ni bloques que el usuario no pidió modificar.
- Para cambiar el formato usa exactamente "16:9", "9:16" o "1:1" en las cadenas existentes.
- Para la calidad usa "low_quality", "medium_quality" o "high_quality".
- `reply`: español, máximo dos frases, sin mencionar JSON ni implementación.
- `summary`: lista corta de etiquetas como formato, calidad, ritmo, función, color o título.
- Si la petición es ambigua o no se puede aplicar, devuelve {"reply": "Pregunta corta aclaratoria.", "summary": [], "code": ""}.
- No incluyas texto fuera del JSON ni bloques Markdown.
"""


def build_code_user_prompt(message: str, path: str, code: str, history: list[dict] | None = None) -> str:
    parts: list[str] = []
    for item in (history or [])[-6:]:
        role = "Usuario" if item.get("role") == "user" else "Asistente"
        parts.append(f"- {role}: {str(item.get('content', ''))[:600]}")
    parts.append(f"Archivo: {path}")
    parts.append("Contenido actual:")
    parts.append(code[:20000])
    parts.append(f"Petición del usuario: {message}")
    return "\n\n".join(parts)


def summarize_patch(patch: dict | None) -> list[str]:
    """Etiquetas legibles para los chips del frontend."""

    if not isinstance(patch, dict):
        return []
    labels: list[str] = []
    for key in patch:
        label = SUMMARY_LABELS.get(key, key)
        if label not in labels:
            labels.append(label)
    return labels


def build_user_prompt(message: str, ir: dict, context: dict | None = None) -> str:
    context = context or {}
    parts: list[str] = []

    history = context.get("history") or []
    if history:
        parts.append("Conversación reciente:")
        for item in history[-6:]:
            role = "Usuario" if item.get("role") == "user" else "Asistente"
            parts.append(f"- {role}: {str(item.get('content', ''))[:600]}")

    last_error = context.get("last_error")
    if last_error:
        parts.append(f"El último render falló con este error: {str(last_error)[:800]}")

    focus = context.get("focus")
    if focus:
        parts.append(f"El usuario estaba editando: {focus}")

    parts.append("IR actual:")
    parts.append(json.dumps(ir, ensure_ascii=False, indent=2)[:12000])
    parts.append(f"Petición del usuario: {message}")
    return "\n\n".join(parts)


def build_repair_prompt(original: Any, error: str) -> str:
    return (
        "Tu respuesta anterior no era válida. Corrígela y vuelve a responder "
        "solo con el JSON exigido.\n\n"
        f"Error de validación: {error}\n\n"
        f"Respuesta anterior: {str(original)[:4000]}"
    )
