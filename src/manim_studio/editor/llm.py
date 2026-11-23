"""Capa LLM abstracta para el asistente de código.

El proveedor devuelve JSON con el archivo completo. El proveedor local
(:class:`MockProvider`) funciona sin red; el remoto habla con cualquier API
compatible con OpenAI. Ninguno de los dos recibe una representación
intermedia: la fuente de verdad es el buffer del editor y el contexto adicional
es solo lectura.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Any, Callable, Protocol

from manim_studio.editor.config import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MAX_TOKENS,
    LLM_MODEL,
    LLM_PROVIDER,
    LLM_TIMEOUT,
)


class LLMProvider(Protocol):
    name: str

    def chat_json(self, messages: list[dict]) -> str:
        ...


class LLMError(RuntimeError):
    """Fallo de red, API o formato de la respuesta del modelo."""


class MockProvider:
    """Proveedor de desarrollo: no hace red, solo marca la respuesta como local."""

    name = "mock"


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

    def _chat(self, messages: list[dict]) -> str:
        payload: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": self.max_tokens,
            "response_format": {"type": "json_object"},
        }
        try:
            data = self._request(payload)
        except LLMError:
            # Algunos proveedores locales no soportan `response_format`.
            simple_payload = {key: value for key, value in payload.items() if key != "response_format"}
            data = self._request(simple_payload)
        try:
            return data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError("El proveedor LLM devolvió una respuesta inesperada.") from exc

    def chat_json(self, messages: list[dict]) -> str:
        """Devuelve el contenido JSON de un intercambio arbitrario."""

        return self._chat(messages)


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
    name = getattr(provider, "name", configured)
    return {
        "provider": name,
        "configured": configured,
        "mock": name == "mock",
        "model": getattr(provider, "model", None),
    }
