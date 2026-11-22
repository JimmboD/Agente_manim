"""Rutas HTTP del estudio: archivos, plantillas y propuestas de código."""

from __future__ import annotations

import traceback

from manim_studio.editor import workspace
from manim_studio.editor.api import ApiError, _read_json, _send_json
from manim_studio.editor.code_assistant import CodeAssistantError, propose_code_change


class WorkspaceAPI:
    def __init__(self, llm=None):
        self.llm = llm

    def handle(self, handler, method: str, path: str, query: dict, body: bytes) -> bool:
        segments = [segment for segment in path.split("/") if segment]
        if len(segments) < 3 or segments[:2] != ["api", "workspace"]:
            return False
        rest = segments[2:]
        try:
            payload = _read_json(body) if method in {"POST", "PUT"} else {}
            if method == "GET":
                self._get(handler, rest, query)
            elif method == "POST":
                self._post(handler, rest, payload)
            else:
                raise ApiError(405, f"Método no soportado: {method}")
        except (ApiError, workspace.WorkspaceError, CodeAssistantError) as exc:
            status = getattr(exc, "status", 500)
            _send_json(handler, status, {"error": getattr(exc, "message", str(exc))})
        except Exception as exc:
            traceback.print_exc()
            _send_json(handler, 500, {"error": f"Error interno: {exc}"})
        return True

    def _get(self, handler, rest: list[str], query: dict) -> None:
        if rest == ["files", "tree"]:
            _send_json(handler, 200, workspace.tree())
            return
        if rest == ["files", "read"]:
            target = (query.get("path") or [""])[0]
            _send_json(handler, 200, workspace.read(target))
            return
        if rest == ["templates"]:
            _send_json(handler, 200, workspace.templates())
            return
        raise ApiError(404, "Ruta de espacio de trabajo no encontrada.")

    def _post(self, handler, rest: list[str], payload: dict) -> None:
        if rest == ["files", "write"]:
            result = workspace.write(
                str(payload.get("path", "")),
                str(payload.get("code", "")),
                payload.get("sha256"),
            )
            _send_json(handler, 200, result)
            return
        if rest == ["files", "create"]:
            result = workspace.create(
                str(payload.get("path", "")),
                str(payload.get("kind", "file")),
            )
            _send_json(handler, 201, result)
            return
        if rest == ["files", "move"]:
            result = workspace.move(
                str(payload.get("from", "")),
                str(payload.get("to", "")),
            )
            _send_json(handler, 200, result)
            return
        if rest == ["files", "delete"]:
            result = workspace.delete(str(payload.get("path", "")))
            _send_json(handler, 200, result)
            return
        if rest == ["files", "upload"]:
            result = workspace.upload_audio(
                str(payload.get("name", "")),
                str(payload.get("data", "")),
            )
            _send_json(handler, 201, result)
            return
        if rest == ["templates"]:
            result = workspace.create_template(
                str(payload.get("name", "")),
                str(payload.get("code", "")),
            )
            _send_json(handler, 201, {"template": result})
            return
        if rest == ["code", "propose"]:
            result = propose_code_change(
                str(payload.get("message", "")),
                str(payload.get("path", "escenas/main.py")),
                str(payload.get("code", "")),
                provider=self.llm,
                history=payload.get("history") if isinstance(payload.get("history"), list) else [],
            )
            _send_json(handler, 200, result)
            return
        if rest == ["code", "apply"]:
            result = workspace.write(
                str(payload.get("path", "")),
                str(payload.get("code", "")),
                payload.get("sha256"),
            )
            _send_json(handler, 200, result)
            return
        raise ApiError(404, "Ruta de espacio de trabajo no encontrada.")
