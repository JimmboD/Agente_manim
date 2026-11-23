"""Helpers HTTP compartidos por las rutas del estudio.

Este módulo sustituye al antiguo ``editor.api``: solo contiene la lectura y
escritura de JSON necesarias para que ``WorkspaceAPI`` responda peticiones.
"""

from __future__ import annotations

import json


class ApiError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def send_json(handler, status: int, payload: dict) -> None:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.send_cors_headers()
    handler.end_headers()
    handler.wfile.write(data)


def read_json(body: bytes) -> dict:
    if not body:
        return {}
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ApiError(400, f"JSON inválido: {exc}") from exc
    if not isinstance(payload, dict):
        raise ApiError(400, "El cuerpo debe ser un objeto JSON.")
    return payload
