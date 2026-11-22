"""Propuestas de código para el estudio.

A diferencia del editor de escenas, aquí la fuente de verdad es el archivo
``.py`` abierto. El modelo (o el proveedor local de desarrollo) devuelve el
archivo completo; el servidor valida la sintaxis y calcula el diff, pero no
guarda nada hasta que el usuario pulsa «Aplicar».
"""

from __future__ import annotations

import ast
import difflib
import re
from dataclasses import dataclass, field
from typing import Any

from manim_studio.editor.llm import (
    LLMError,
    MockProvider,
    get_provider,
    parse_llm_response,
)
from manim_studio.editor.prompts import CODE_SYSTEM_PROMPT, build_code_user_prompt

MAX_CODE_CHARS = 60_000
MAX_DIFF_CHARS = 12_000

COLOR_WORDS = {
    "verde": "#83C167",
    "azul": "#58C4DD",
    "amarillo": "#FFFF00",
    "rojo": "#FC6255",
    "blanco": "#FFFFFF",
}


@dataclass
class CodeProposal:
    reply: str
    code: str
    summary: list[str] = field(default_factory=list)
    code_diff: str = ""
    provider: str = "mock"
    fallback: str | None = None


class CodeAssistantError(ValueError):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def make_diff(before: str, after: str, path: str) -> str:
    lines = list(
        difflib.unified_diff(
            before.splitlines(),
            after.splitlines(),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
            lineterm="",
        )
    )
    diff = "\n".join(lines)
    return diff[:MAX_DIFF_CHARS] if len(diff) > MAX_DIFF_CHARS else diff


def validate_code(code: str) -> str:
    if not isinstance(code, str) or not code.strip():
        raise CodeAssistantError(422, "El modelo no devolvió código Python.")
    if len(code) > MAX_CODE_CHARS:
        raise CodeAssistantError(413, "El código propuesto es demasiado grande.")
    try:
        ast.parse(code)
    except SyntaxError as exc:
        raise CodeAssistantError(422, f"El código propuesto no es válido: {exc}") from exc
    return code


def _inject_lines(code: str, lines: list[str]) -> str:
    """Inserta líneas respetando docstring inicial y `from __future__`."""

    prefix = "\n".join(lines)
    working = code
    head = ""
    if working.startswith('"""') or working.startswith("'''"):
        quote = working[:3]
        end = working.find(quote, 3)
        if end > 0:
            end += 3
            head = working[:end]
            working = working[end:].lstrip("\n")
    future_lines: list[str] = []
    while True:
        first, separator, remainder = working.partition("\n")
        if first.startswith("from __future__ import"):
            future_lines.append(first)
            working = remainder
        else:
            break
    parts = [head, *future_lines, prefix, working]
    return "\n".join(part for part in parts if part)


def _mock_proposal(message: str, code: str, path: str) -> CodeProposal | None:
    text = (message or "").strip()
    lower = text.lower()
    if not text:
        return None

    new_code = code
    notes: list[str] = []
    summary: list[str] = []
    injections: list[str] = []

    for fmt in ("16:9", "9:16", "1:1"):
        if fmt in text:
            found = False
            for other in ("16:9", "9:16", "1:1"):
                if other in new_code:
                    found = True
                    new_code = new_code.replace(other, fmt)
            if not found:
                injections.append('import os')
                injections.append(f'os.environ["MANIM_FORMAT"] = "{fmt}"')
            notes.append(f"cambié el formato a {fmt}")
            summary.append("formato")
            break

    match = re.search(r"(\d+)\s*(iteraciones|iteración|iteracion)", lower)
    if match:
        number = match.group(1)
        replaced = re.sub(r"(?im)^(MAX_ITERATIONS|MAX_ITERACIONES|max_iterations)\s*=\s*\d+", rf"\1 = {number}", new_code)
        if replaced == new_code:
            injections.append(f"# Iteraciones solicitadas: {number}")
        new_code = replaced
        notes.append(f"ajusté las iteraciones a {number}")
        summary.append("iteraciones")

    if any(word in lower for word in ("más rápido", "mas rapido", "acelera", "acorta")):
        injections.append("# Ritmo: acelerado un 20 %")
        notes.append("aceleré el ritmo")
        summary.append("ritmo")
    elif any(word in lower for word in ("más lento", "mas lento", "pausado", "respira")):
        injections.append("# Ritmo: ralentizado un 25 %")
        notes.append("ralenticé el ritmo")
        summary.append("ritmo")

    for word, color in COLOR_WORDS.items():
        if word in lower:
            injections.append(f"# Color solicitado: {word} ({color})")
            notes.append(f"puse el color {word}")
            summary.append("color")
            break

    if any(word in lower for word in ("título", "titulo")):
        title_match = re.search(r"(?:t[ií]tulo|titulo)\s*(?:a|:)?\s*(.+)$", text, re.IGNORECASE)
        if title_match:
            injections.append(f"# Título: {title_match.group(1).strip()[:80]}")
            notes.append("actualicé el título")
            summary.append("título")

    if not notes:
        return None

    if injections:
        new_code = _inject_lines(new_code, injections)
    new_code = validate_code(new_code)
    return CodeProposal(
        reply="Hecho: " + ", ".join(notes) + ".",
        code=new_code,
        summary=list(dict.fromkeys(summary))[:8],
        code_diff=make_diff(code, new_code, path),
        provider="mock",
    )


def _parse_provider_payload(data: dict) -> CodeProposal:
    reply = data.get("reply")
    if not isinstance(reply, str) or not reply.strip():
        raise LLMError("La respuesta del modelo no incluye `reply`.")
    summary = data.get("summary", [])
    if not isinstance(summary, list):
        summary = []
    summary = [str(item)[:40] for item in summary[:8]]
    code = validate_code(data.get("code", ""))
    return CodeProposal(reply=reply.strip()[:800], code=code, summary=summary)


def propose_code_change(
    message: str,
    path: str,
    code: str,
    *,
    provider: Any | None = None,
    history: list[dict] | None = None,
) -> dict:
    """Devuelve una propuesta sin guardar. Nunca lanza excepciones de red."""

    message = (message or "").strip()
    if not message:
        raise CodeAssistantError(400, "Escribe qué quieres cambiar del código.")
    code = validate_code(code)
    provider = provider or get_provider()
    fallback: str | None = None

    proposal: CodeProposal | None = None
    if isinstance(provider, MockProvider):
        proposal = _mock_proposal(message, code, path)
    else:
        chat_json = getattr(provider, "chat_json", None)
        if chat_json:
            try:
                messages = [
                    {"role": "system", "content": CODE_SYSTEM_PROMPT},
                    {"role": "user", "content": build_code_user_prompt(message, path, code, history)},
                ]
                parsed = _parse_provider_payload(parse_llm_response(chat_json(messages)))
                parsed.code_diff = make_diff(code, parsed.code, path)
                parsed.provider = getattr(provider, "name", "llm")
                proposal = parsed
            except (LLMError, CodeAssistantError) as exc:
                fallback = f"(Proveedor LLM no disponible: usé respuestas locales: {exc})"

    if proposal is None:
        proposal = _mock_proposal(message, code, path)
    if proposal is None:
        raise CodeAssistantError(
            400,
            "No entendí el cambio. Prueba con: formato 9:16, 3 iteraciones, más rápido o un color.",
        )

    return {
        "reply": proposal.reply,
        "summary": proposal.summary,
        "code": proposal.code,
        "code_diff": proposal.code_diff or "Sin cambios en el código.",
        "provider": proposal.provider,
        "fallback": fallback,
        "path": path,
    }
