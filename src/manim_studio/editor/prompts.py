"""Prompts del asistente de código del Estudio.

El buffer del editor siempre es la fuente de verdad. Los archivos adicionales
que lleguen como contexto son solo lectura: no pueden ser modificados por la
propuesta. Solo se admiten propuestas para el archivo activo si es ``.py`` o
``.txt``.
"""

from __future__ import annotations

BUFFER_CHARS = 20_000


CODE_SYSTEM_PROMPT = """Eres el asistente de código de Manim Studio.

Trabajas SIEMPRE sobre el archivo activo que se te pasa en el mensaje. Ese
archivo es el buffer del editor y es la fuente de verdad. El resto de archivos
que aparezcan bajo «Contexto adicional» son SOLO LECTURA: sirven para entender,
pero NO debes proponer cambios en ellos.

Solo puedes recibir un archivo activo .py o .txt:
- Si es .py: devuelve el archivo Python COMPLETO con sintaxis válida.
- Si es .txt: devuelve el contenido textual COMPLETO (por ejemplo, las líneas
  LaTeX de un archivo de pasos algebraicos). No añadas comentarios Python ni
  código ejecutable.

Responde ÚNICAMENTE un objeto JSON con esta forma exacta:
{"reply": "...", "summary": ["formato"], "code": "archivo completo"}

Reglas:
- Haz únicamente el cambio que pidió el usuario; conserva el resto del archivo.
- `code` debe contener el archivo COMPLETO, nunca un fragmento ni un diff.
- `reply`: español, máximo dos frases, sin mencionar JSON ni implementación.
- `summary`: lista corta de etiquetas como formato, calidad, ritmo, función,
  color, título o pasos.
- Si la petición es ambigua o no se puede aplicar, devuelve
  {"reply": "Pregunta corta aclaratoria.", "summary": [], "code": ""}.
- No incluyas texto fuera del JSON ni bloques Markdown.
"""


def build_code_user_prompt(
    message: str,
    path: str,
    code: str,
    history: list[dict] | None = None,
    context_files: list[dict] | None = None,
) -> str:
    """Serializa el buffer activo y el contexto adicional de solo lectura."""

    parts: list[str] = []
    for item in (history or [])[-6:]:
        role = "Usuario" if item.get("role") == "user" else "Asistente"
        parts.append(f"- {role}: {str(item.get('content', ''))[:600]}")
    if len(parts):
        parts.insert(0, "Conversación reciente:")

    parts.append("Archivo activo (buffer del editor, fuente de verdad):")
    parts.append(f"--- {path} ---")
    parts.append(str(code)[:BUFFER_CHARS])

    if context_files:
        parts.append("Contexto adicional (SOLO LECTURA; no propongas cambios aquí):")
        for item in context_files:
            item_path = str(item.get("path", ""))
            item_code = str(item.get("code", ""))
            note = " [recortado]" if item.get("truncated") else ""
            parts.append(f"--- {item_path}{note} ---")
            parts.append(item_code)

    parts.append(f"Petición del usuario: {message}")
    return "\n\n".join(parts)
