"""Propuestas de código para el Estudio.

La fuente de verdad es el archivo abierto en el editor. El modelo (o el
proveedor local de desarrollo) devuelve el archivo completo; el servidor valida
el contenido y calcula el diff, pero no guarda nada hasta que el usuario pulsa
«Aplicar». Solo se proponen cambios en archivos ``.py`` o ``.txt``.
"""

from __future__ import annotations

import ast
import difflib
import re
from dataclasses import dataclass, field
from pathlib import Path
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
MAX_DIFF_ROWS = 400
CONTEXT_LINES = 3
EDITABLE_SUFFIXES = {".py", ".txt"}

COLOR_WORDS = {
    "verde": "#83C167",
    "azul": "#58C4DD",
    "amarillo": "#FFFF00",
    "rojo": "#FC6255",
    "blanco": "#FFFFFF",
}

LATEX_COLORS = {
    "verde": "green",
    "azul": "blue",
    "amarillo": "yellow",
    "rojo": "red",
    "blanco": "white",
}


@dataclass
class CodeProposal:
    reply: str
    code: str
    summary: list[str] = field(default_factory=list)
    code_diff: str = ""
    hunks: list[dict] = field(default_factory=list)
    stats: dict = field(default_factory=lambda: {"added": 0, "removed": 0})
    provider: str = "mock"
    fallback: str | None = None


class CodeAssistantError(ValueError):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def ensure_editable_path(path: str) -> str:
    """Rechaza cualquier archivo activo que no sea .py o .txt."""

    suffix = Path(str(path or "")).suffix.lower()
    if suffix not in EDITABLE_SUFFIXES:
        raise CodeAssistantError(
            422, "Solo se pueden proponer cambios en archivos .py o .txt."
        )
    return str(path)


def validate_proposal(path: str, content: str) -> str:
    """Valida el contenido completo según el tipo de archivo activo."""

    ensure_editable_path(path)
    if not isinstance(content, str) or not content.strip():
        raise CodeAssistantError(422, "El modelo no devolvió contenido.")
    if len(content) > MAX_CODE_CHARS:
        raise CodeAssistantError(413, "El contenido propuesto es demasiado grande.")
    try:
        content.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise CodeAssistantError(422, "El contenido propuesto no es UTF-8 válido.") from exc

    if Path(path).suffix.lower() == ".py":
        try:
            ast.parse(content)
        except SyntaxError as exc:
            raise CodeAssistantError(422, f"El código propuesto no es válido: {exc}") from exc
    return content


def validate_code(code: str, path: str = "escenas/main.py") -> str:
    """Alias compatible con la validación Python-only de versiones anteriores."""

    return validate_proposal(path, code)


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


def make_diff_details(before: str, after: str, path: str) -> tuple[list[dict], dict]:
    """Filas de diff para resaltado tipo GitHub, agrupadas por fragmentos."""

    old_lines = before.splitlines()
    new_lines = after.splitlines()
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False)
    opcodes = matcher.get_opcodes()

    rows: list[dict] = []
    stats = {"added": 0, "removed": 0}
    for tag, i1, i2, j1, j2 in opcodes:
        if tag == "equal":
            for offset in range(i2 - i1):
                rows.append(
                    {
                        "type": "context",
                        "old": i1 + offset + 1,
                        "new": j1 + offset + 1,
                        "text": old_lines[i1 + offset],
                    }
                )
        elif tag == "delete":
            stats["removed"] += i2 - i1
            for offset in range(i2 - i1):
                rows.append(
                    {
                        "type": "remove",
                        "old": i1 + offset + 1,
                        "new": None,
                        "text": old_lines[i1 + offset],
                    }
                )
        elif tag == "insert":
            stats["added"] += j2 - j1
            for offset in range(j2 - j1):
                rows.append(
                    {
                        "type": "add",
                        "old": None,
                        "new": j1 + offset + 1,
                        "text": new_lines[j1 + offset],
                    }
                )
        else:
            stats["removed"] += i2 - i1
            stats["added"] += j2 - j1
            for offset in range(i2 - i1):
                rows.append(
                    {
                        "type": "remove",
                        "old": i1 + offset + 1,
                        "new": None,
                        "text": old_lines[i1 + offset],
                    }
                )
            for offset in range(j2 - j1):
                rows.append(
                    {
                        "type": "add",
                        "old": None,
                        "new": j1 + offset + 1,
                        "text": new_lines[j1 + offset],
                    }
                )

    changed = [index for index, row in enumerate(rows) if row["type"] != "context"]
    if not changed:
        return [], stats
    if stats["added"] == 0 and stats["removed"] == 0:
        return [], stats

    ranges: list[tuple[int, int]] = []
    for index in changed:
        start = max(0, index - CONTEXT_LINES)
        end = min(len(rows), index + CONTEXT_LINES + 1)
        if ranges and start <= ranges[-1][1]:
            ranges[-1] = (ranges[-1][0], max(ranges[-1][1], end))
        else:
            ranges.append((start, end))

    hunks: list[dict] = []
    for start, end in ranges[:MAX_DIFF_ROWS]:
        fragment = rows[start:end]
        old_numbers = [row["old"] for row in fragment if row["old"] is not None]
        new_numbers = [row["new"] for row in fragment if row["new"] is not None]
        hunks.append(
            {
                "old_start": min(old_numbers) if old_numbers else 0,
                "new_start": min(new_numbers) if new_numbers else 0,
                "old_count": len(old_numbers),
                "new_count": len(new_numbers),
                "lines": fragment,
            }
        )
    return hunks, stats


def build_diff(before: str, after: str, path: str) -> tuple[str, list[dict], dict]:
    hunks, stats = make_diff_details(before, after, path)
    return make_diff(before, after, path), hunks, stats


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


def _mock_python_proposal(message: str, code: str, path: str) -> CodeProposal | None:
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
    new_code = validate_proposal(path, new_code)
    diff, hunks, stats = build_diff(code, new_code, path)
    return CodeProposal(
        reply="Hecho: " + ", ".join(notes) + ".",
        code=new_code,
        summary=list(dict.fromkeys(summary))[:8],
        code_diff=diff,
        hunks=hunks,
        stats=stats,
        provider="mock",
    )


def _mock_text_proposal(message: str, code: str, path: str) -> CodeProposal | None:
    """Heurística local para archivos de texto/LaTeX (sin ast.parse)."""

    text = (message or "").strip()
    lower = text.lower()
    if not text:
        return None

    new_code = code
    notes: list[str] = []
    summary: list[str] = []

    for word, latex_color in LATEX_COLORS.items():
        if word in lower:
            replaced, count = re.subn(
                r"\\textcolor\{[^}]*\}", f"\\\\textcolor{{{latex_color}}}", new_code
            )
            if count:
                new_code = replaced
                notes.append(f"puse el color {word} en las fórmulas")
            else:
                new_code = new_code.rstrip() + f"\n% Color solicitado: {word}"
                notes.append(f"anoté el color {word}")
            summary.append("color")
            break

    match = re.search(r"(\d+)\s*(iteraciones|iteración|iteracion)", lower)
    if match:
        new_code = new_code.rstrip() + f"\n% Iteraciones: {match.group(1)}"
        notes.append(f"anoté {match.group(1)} iteraciones")
        summary.append("iteraciones")

    for fmt in ("16:9", "9:16", "1:1"):
        if fmt in text:
            new_code = new_code.rstrip() + f"\n% Formato: {fmt}"
            notes.append(f"anoté el formato {fmt}")
            summary.append("formato")
            break

    if any(word in lower for word in ("más rápido", "mas rapido", "acelera", "acorta")):
        new_code = new_code.rstrip() + "\n% Ritmo: acelerado un 20 %"
        notes.append("aceleré el ritmo")
        summary.append("ritmo")
    elif any(word in lower for word in ("más lento", "mas lento", "pausado", "respira")):
        new_code = new_code.rstrip() + "\n% Ritmo: ralentizado un 25 %"
        notes.append("ralenticé el ritmo")
        summary.append("ritmo")

    if any(word in lower for word in ("título", "titulo")):
        title_match = re.search(r"(?:t[ií]tulo|titulo)\s*(?:a|:)?\s*(.+)$", text, re.IGNORECASE)
        if title_match:
            new_code = new_code.rstrip() + f"\n% Título: {title_match.group(1).strip()[:80]}"
            notes.append("actualicé el título")
            summary.append("título")

    if not notes:
        return None

    new_code = validate_proposal(path, new_code)
    diff, hunks, stats = build_diff(code, new_code, path)
    return CodeProposal(
        reply="Hecho: " + ", ".join(notes) + ".",
        code=new_code,
        summary=list(dict.fromkeys(summary))[:8],
        code_diff=diff,
        hunks=hunks,
        stats=stats,
        provider="mock",
    )


def _mock_proposal(message: str, code: str, path: str) -> CodeProposal | None:
    if Path(path).suffix.lower() == ".txt":
        return _mock_text_proposal(message, code, path)
    return _mock_python_proposal(message, code, path)


def _parse_provider_payload(data: dict, path: str) -> CodeProposal:
    reply = data.get("reply")
    if not isinstance(reply, str) or not reply.strip():
        raise LLMError("La respuesta del modelo no incluye `reply`.")
    summary = data.get("summary", [])
    if not isinstance(summary, list):
        summary = []
    summary = [str(item)[:40] for item in summary[:8]]
    code = validate_proposal(path, data.get("code", ""))
    return CodeProposal(reply=reply.strip()[:800], code=code, summary=summary)


def propose_code_change(
    message: str,
    path: str,
    code: str,
    *,
    provider: Any | None = None,
    history: list[dict] | None = None,
    context_files: list[dict] | None = None,
) -> dict:
    """Devuelve una propuesta sin guardar. Nunca lanza excepciones de red."""

    message = (message or "").strip()
    if not message:
        raise CodeAssistantError(400, "Escribe qué quieres cambiar del código.")
    ensure_editable_path(path)
    code = validate_proposal(path, code)
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
                    {
                        "role": "user",
                        "content": build_code_user_prompt(
                            message, path, code, history, context_files
                        ),
                    },
                ]
                parsed = _parse_provider_payload(
                    parse_llm_response(chat_json(messages)), path
                )
                parsed.code_diff, parsed.hunks, parsed.stats = build_diff(
                    code, parsed.code, path
                )
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
        "hunks": proposal.hunks,
        "stats": proposal.stats,
        "provider": proposal.provider,
        "fallback": fallback,
        "path": path,
    }
