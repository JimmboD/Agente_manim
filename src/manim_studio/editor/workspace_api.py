"""Rutas HTTP del estudio: proyectos, archivos, plantillas y código."""

from __future__ import annotations

import traceback

from manim_studio.editor import projects, workspace
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
                self._post(handler, rest, payload, query)
            else:
                raise ApiError(405, f"Método no soportado: {method}")
        except (ApiError, workspace.WorkspaceError, CodeAssistantError, projects.ProjectError) as exc:
            status = getattr(exc, "status", 500)
            _send_json(handler, status, {"error": getattr(exc, "message", str(exc))})
        except Exception as exc:
            traceback.print_exc()
            _send_json(handler, 500, {"error": f"Error interno: {exc}"})
        return True

    @staticmethod
    def _project(payload: dict | None = None, query: dict | None = None) -> str:
        payload = payload or {}
        query = query or {}
        from_payload = str(payload.get("project") or "").strip()
        from_query = str((query.get("project") or [""])[0] or "").strip()
        return from_payload or from_query or projects.active_slug()

    def _get(self, handler, rest: list[str], query: dict) -> None:
        workspace.set_project(self._project({}, query))
        if rest == ["projects"]:
            _send_json(
                handler,
                200,
                {
                    "projects": projects.list_projects(),
                    "active": projects.active_slug(),
                    "settings": projects.get_settings(),
                },
            )
            return
        if rest == ["settings"]:
            _send_json(handler, 200, projects.get_settings())
            return
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

    def _post(self, handler, rest: list[str], payload: dict, query: dict) -> None:
        workspace.set_project(self._project(payload, query))
        if rest == ["projects"]:
            result = projects.create_project(str(payload.get("title", "")))
            workspace.set_project(result["slug"])
            _send_json(handler, 201, {"project": result})
            return
        if rest == ["projects", "select"]:
            result = projects.set_active(str(payload.get("slug", "")))
            workspace.set_project(result["slug"])
            _send_json(handler, 200, result)
            return
        if rest == ["projects", "delete"]:
            result = projects.delete_project(str(payload.get("slug", "")))
            workspace.set_project(result["active"])
            _send_json(handler, 200, result)
            return
        if rest == ["settings"]:
            result = projects.update_settings(payload)
            workspace.set_system_templates_unlocked(result["unlockSystemTemplates"])
            _send_json(handler, 200, result)
            return
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
