"""Capa LLM abstracta.

En el MVP solo existe `MockProvider`: interpreta órdenes sencillas en español y
devuelve un parche sobre el IR. Un proveedor real solo tendrá que implementar
`LLMProvider.propose`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class LLMProposal:
    reply: str
    patch: dict = field(default_factory=dict)
    code_diff: str | None = None


class LLMProvider(Protocol):
    name: str

    def propose(self, message: str, ir: dict, context: dict | None = None) -> LLMProposal:
        ...


def _normalize_function_text(text: str) -> str:
    text = text.strip().strip("$").strip()
    text = text.replace("^", "**")
    text = text.replace("π", "math.pi")
    text = re.sub(r"\bsen\s*\(", "sin(", text)
    text = re.sub(r"\bln\s*\(", "log(", text)
    text = re.sub(r"(?<=\d)(?=[a-zA-Z(])", "*", text)
    return text


class MockProvider:
    """Proveedor de desarrollo: heurísticas, sin red ni API keys."""

    name = "mock"

    def propose(self, message: str, ir: dict, context: dict | None = None) -> LLMProposal:
        text = (message or "").strip()
        lower = text.lower()
        patch: dict = {}
        notes: list[str] = []

        if not text:
            return LLMProposal("Escribe qué quieres cambiar de la escena.")

        # Velocidad global.
        if any(word in lower for word in ("más rápido", "mas rapido", "acelera", "acorta")):
            beats = [
                {
                    **beat,
                    "t_anim": max(0.1, round(beat["t_anim"] * 0.8, 2)),
                    "t_wait": max(0.0, round(beat["t_wait"] * 0.8, 2)),
                }
                for beat in ir.get("beats", [])
            ]
            patch["beats"] = beats
            notes.append("reduje los tiempos un 20 %")
        elif any(word in lower for word in ("más lento", "mas lento", "pausado", "respira")):
            beats = [
                {
                    **beat,
                    "t_anim": min(10.0, round(beat["t_anim"] * 1.25, 2)),
                    "t_wait": min(10.0, round(beat["t_wait"] * 1.25, 2)),
                }
                for beat in ir.get("beats", [])
            ]
            patch["beats"] = beats
            notes.append("aumenté los tiempos un 25 %")

        # Formato.
        for format_id in ("16:9", "9:16", "1:1"):
            if format_id in text:
                patch["format"] = format_id
                notes.append(f"cambié el formato a {format_id}")
                break

        # Iteraciones.
        match = re.search(r"(\d+)\s*(iteraciones|iteración|iteracion)", lower)
        if match:
            patch.setdefault("params", {})["max_iterations"] = int(match.group(1))
            notes.append(f"ajusté las iteraciones a {match.group(1)}")

        # Tolerancia.
        match = re.search(r"tolerancia\s*(?:=|a|de)?\s*([0-9.eE+-]+)", lower)
        if match:
            try:
                patch.setdefault("params", {})["tolerance"] = float(match.group(1))
                notes.append("actualicé la tolerancia")
            except ValueError:
                pass

        # Intervalo [a, b] o a=..., b=...
        match = re.search(r"\[\s*(-?[0-9.]+)\s*,\s*(-?[0-9.]+)\s*\]", text)
        if match:
            patch.setdefault("params", {})["a"] = float(match.group(1))
            patch.setdefault("params", {})["b"] = float(match.group(2))
            notes.append(f"cambié el intervalo a [{match.group(1)}, {match.group(2)}]")
        else:
            for name in ("a", "b"):
                match = re.search(rf"\b{name}\s*=\s*(-?[0-9.]+)", lower)
                if match:
                    patch.setdefault("params", {})[name] = float(match.group(1))
                    notes.append(f"cambié {name} a {match.group(1)}")

        # Función: "función f(x) = ..." o "cambia la función a ...".
        match = re.search(r"f\s*\(x\)\s*=\s*(.+)$", text, re.IGNORECASE)
        if not match:
            match = re.search(r"(?:función|funcion)\s*(?:a|:)?\s*(.+)$", text, re.IGNORECASE)
        if match:
            expression = _normalize_function_text(match.group(1))
            patch.setdefault("function", {})["python"] = expression
            patch.setdefault("function", {})["latex"] = rf"f(x) = {expression}"
            notes.append("actualicé la función")

        # Color de resultado.
        if "verde" in lower:
            patch.setdefault("layout", {})["result_color"] = "#a6e3a1"
            notes.append("puse el resultado en verde")
        elif "azul" in lower:
            patch.setdefault("layout", {})["accent"] = "#89b4fa"
            notes.append("puse el acento en azul")

        # Título.
        match = re.search(r"t[ií]tulo\s*(?:a|:)?\s*(.+)$", text, re.IGNORECASE)
        if match:
            patch["title"] = match.group(1).strip()[:120]
            notes.append("cambié el título")

        if not patch:
            return LLMProposal(
                "Puedo ajustar tiempos, formato (16:9, 9:16, 1:1), iteraciones, "
                "tolerancia, intervalo [a, b], la función o el color del resultado. "
                "Dime qué cambio quieres."
            )

        reply = "Hecho: " + ", ".join(notes) + "."
        return LLMProposal(reply=reply, patch=patch)


def get_provider(name: str = "mock") -> LLMProvider:
    providers = {"mock": MockProvider}
    if name not in providers:
        raise ValueError(f"Proveedor LLM no disponible: {name}")
    return providers[name]()
