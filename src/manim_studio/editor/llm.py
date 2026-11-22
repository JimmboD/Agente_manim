"""Capa LLM abstracta.

`MockProvider` interpreta órdenes sencillas sin red; `OpenAICompatibleProvider`
habla con cualquier API compatible con OpenAI (OpenAI, DeepSeek, OpenRouter,
Ollama). Ambos devuelven un parche sobre el IR, nunca código Python.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

from manim_studio.editor.config import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MAX_TOKENS,
    LLM_MODEL,
    LLM_PROVIDER,
    LLM_TIMEOUT,
)
from manim_studio.editor.prompts import SYSTEM_PROMPT, build_repair_prompt, build_user_prompt


@dataclass
class LLMProposal:
    reply: str
    patch: dict = field(default_factory=dict)
    summary: list[str] = field(default_factory=list)
    code_diff: str | None = None


class LLMProvider(Protocol):
    name: str

    def propose(self, message: str, ir: dict, context: dict | None = None) -> LLMProposal:
        ...


class LLMError(RuntimeError):
    """Fallo de red, API o formato de la respuesta del modelo."""


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


def parse_llm_response(text: str) -> dict:
    """Extrae un objeto JSON de una respuesta, tolerando bloques ```json."""

    if not isinstance(text, str) or not text.strip():
        raise LLMError("El modelo devolvió una respuesta vacía.")

    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end <= start:
        raise LLMError("El modelo no devolvió un objeto JSON.")

    try:
        data: Any = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError as exc:
        raise LLMError(f"JSON inválido del modelo: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise LLMError("La respuesta del modelo debe ser un objeto JSON.")
    return data


def proposal_from_payload(data: dict) -> LLMProposal:
    reply = data.get("reply")
    if not isinstance(reply, str) or not reply.strip():
        raise LLMError("La respuesta del modelo no incluye `reply`.")
    patch = data.get("patch", {})
    if patch is None:
        patch = {}
    if not isinstance(patch, dict):
        raise LLMError("`patch` debe ser un objeto JSON.")
    summary = data.get("summary", [])
    if not isinstance(summary, list):
        summary = []
    summary = [str(item)[:40] for item in summary[:8]]
    return LLMProposal(reply=reply.strip()[:800], patch=patch, summary=summary)


class OpenAICompatibleProvider:
    """Proveedor LLM genérico sobre la API de chat/completions."""

    name = "openai"

    def __init__(
        self,
        *,
        base_url: str = LLM_BASE_URL,
        model: str = LLM_MODEL,
        api_key: str = LLM_API_KEY,
        timeout: float = LLM_TIMEOUT,
        max_tokens: int = LLM_MAX_TOKENS,
        opener: Callable | None = None,
    ):
        self.base_url = (base_url or LLM_BASE_URL).rstrip("/")
        self.model = model or LLM_MODEL
        self.api_key = api_key
        self.timeout = timeout
        self.max_tokens = max_tokens
        self._opener = opener or urllib.request.urlopen
        self.name = f"openai:{self.model}"

    def _request(self, payload: dict) -> dict:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "ManimStudioEditor/1.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with self._opener(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                detail = exc.read().decode("utf-8", errors="replace")[:400]
            except Exception:
                detail = ""
            raise LLMError(f"HTTP {exc.code} del proveedor LLM: {detail}") from exc
        except (urllib.error.URLError, OSError, TimeoutError, ValueError) as exc:
            raise LLMError(f"No se pudo contactar al proveedor LLM: {exc}") from exc

        try:
            data: Any = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LLMError(f"Respuesta no JSON del proveedor LLM: {exc.msg}") from exc
        if not isinstance(data, dict):
            raise LLMError("Respuesta inesperada del proveedor LLM.")
        if "error" in data:
            raise LLMError(f"Error del proveedor LLM: {data['error']}")
        return data

    def _chat(self, messages: list[dict], *, structured: bool) -> str:
        payload: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": self.max_tokens,
        }
        if structured:
            payload["response_format"] = {"type": "json_object"}
        try:
            data = self._request(payload)
        except LLMError:
            if not structured:
                raise
            # Algunos proveedores locales no soportan `response_format`.
            simple_payload = {key: value for key, value in payload.items() if key != "response_format"}
            data = self._request(simple_payload)
        try:
            return data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError("El proveedor LLM devolvió una respuesta inesperada.") from exc

    def chat_json(self, messages: list[dict]) -> str:
        """Respuesta JSON de un intercambio arbitrario (usado por el estudio)."""

        return self._chat(messages, structured=True)

    def propose(self, message: str, ir: dict, context: dict | None = None) -> LLMProposal:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(message, ir, context)},
        ]
        raw = self._chat(messages, structured=True)
        return proposal_from_payload(parse_llm_response(raw))

    def repair(self, proposal: LLMProposal, error: str, message: str, ir: dict, context: dict | None = None) -> LLMProposal:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(message, ir, context)},
            {
                "role": "assistant",
                "content": json.dumps(
                    {"reply": proposal.reply, "summary": proposal.summary, "patch": proposal.patch},
                    ensure_ascii=False,
                ),
            },
            {"role": "user", "content": build_repair_prompt(proposal.patch, error)},
        ]
        raw = self._chat(messages, structured=True)
        return proposal_from_payload(parse_llm_response(raw))


def get_provider(name: str | None = None) -> LLMProvider:
    """Construye el proveedor configurado, con fallback seguro a mock."""

    provider_id = (name or LLM_PROVIDER or "mock").strip().lower()
    if provider_id in {"mock", "none", ""}:
        return MockProvider()
    if provider_id in {"openai", "openai-compatible", "openai_compatible", "deepseek", "openrouter", "ollama"}:
        if not LLM_API_KEY and provider_id != "ollama":
            return MockProvider()
        return OpenAICompatibleProvider()
    raise ValueError(f"Proveedor LLM no disponible: {provider_id}")


def provider_info(provider: LLMProvider) -> dict:
    configured = (LLM_PROVIDER or "mock").strip().lower()
    model = getattr(provider, "model", None)
    return {
        "provider": getattr(provider, "name", configured),
        "configured": configured,
        "mock": getattr(provider, "name", configured) == "mock",
        "model": model,
    }
