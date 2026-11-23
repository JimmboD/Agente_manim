"""Rutas HTTP del estudio: proyectos, archivos, plantillas y código."""

from __future__ import annotations

import traceback

from manim_studio.editor import context as context_builder
from manim_studio.editor import projects, template_bundles, workspace
from manim_studio.editor.code_assistant import (
    CodeAssistantError,
    ensure_editable_path,
    propose_code_change,
)
from manim_studio.editor.config import DEFAULT_QUALITY, FORMATS, QUALITIES
from manim_studio.editor.http import ApiError, read_json, send_json
from manim_studio.editor.llm import provider_info
from manim_studio.editor.template_bundles import TemplateConflictError


class WorkspaceAPI:
    def __init__(self, llm=None, token: str | None = None):
        self.llm = llm
        self.token = token

    def handle(self, handler, method: str, path: str, query: dict, body: bytes) -> bool:
        segments = [segment for segment in path.split("/") if segment]
        if len(segments) < 3 or segments[:2] != ["api", "workspace"]:
            return False
        rest = segments[2:]
        try:
            payload = read_json(body) if method in {"POST", "PUT"} else {}
            if method == "GET":
                self._get(handler, rest, query)
            elif method == "POST":
                self._post(handler, rest, payload, query)
            else:
                raise ApiError(405, f"Método no soportado: {method}")
        except TemplateConflictError as exc:
            send_json(
                handler,
                exc.status,
                {
                    "error": exc.message,
                    "conflicts": exc.conflicts,
                    "expected_shas": exc.expected_shas,
                },
            )
        except (
            ApiError,
            workspace.WorkspaceError,
            CodeAssistantError,
            projects.ProjectError,
        ) as exc:
            status = getattr(exc, "status", 500)
            send_json(handler, status, {"error": getattr(exc, "message", str(exc))})
        except Exception as exc:
            traceback.print_exc()
            send_json(handler, 500, {"error": f"Error interno: {exc}"})
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
        if rest == ["bootstrap"]:
            send_json(
                handler,
                200,
                {
                    "token": self.token,
                    "formats": [{"id": key, **value} for key, value in FORMATS.items()],
                    "qualities": [{"id": key, **value} for key, value in QUALITIES.items()],
                    "default_format": "16:9",
                    "default_quality": DEFAULT_QUALITY,
                    "context_modes": sorted(context_builder.MODES),
                    "llm": provider_info(self.llm),
                },
            )
            return
        if rest == ["projects"]:
            send_json(
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
            send_json(handler, 200, projects.get_settings())
            return
        if rest == ["files", "tree"]:
            send_json(handler, 200, workspace.tree())
            return
        if rest == ["files", "read"]:
            target = (query.get("path") or [""])[0]
            send_json(handler, 200, workspace.read(target))
            return
        if rest == ["templates"]:
            send_json(handler, 200, workspace.templates())
            return
        raise ApiError(404, "Ruta de espacio de trabajo no encontrada.")

    def _post(self, handler, rest: list[str], payload: dict, query: dict) -> None:
        workspace.set_project(self._project(payload, query))
        if rest == ["projects"]:
            result = projects.create_project(str(payload.get("title", "")))
            workspace.set_project(result["slug"])
            send_json(handler, 201, {"project": result})
            return
        if rest == ["projects", "select"]:
            result = projects.set_active(str(payload.get("slug", "")))
            workspace.set_project(result["slug"])
            send_json(handler, 200, result)
            return
        if rest == ["projects", "delete"]:
            result = projects.delete_project(str(payload.get("slug", "")))
            workspace.set_project(result["active"])
            send_json(handler, 200, result)
            return
        if rest == ["settings"]:
            result = projects.update_settings(payload)
            workspace.set_system_templates_unlocked(result["unlockSystemTemplates"])
            send_json(handler, 200, result)
            return
        if rest == ["files", "write"]:
            result = workspace.write(
                str(payload.get("path", "")),
                str(payload.get("code", "")),
                payload.get("sha256"),
            )
            send_json(handler, 200, result)
            return
        if rest == ["files", "create"]:
            result = workspace.create(
                str(payload.get("path", "")),
                str(payload.get("kind", "file")),
            )
            send_json(handler, 201, result)
            return
        if rest == ["files", "move"]:
            result = workspace.move(
                str(payload.get("from", "")),
                str(payload.get("to", "")),
            )
            send_json(handler, 200, result)
            return
        if rest == ["files", "delete"]:
            result = workspace.delete(str(payload.get("path", "")))
            send_json(handler, 200, result)
            return
        if rest == ["files", "upload"]:
            result = workspace.upload_audio(
                str(payload.get("name", "")),
                str(payload.get("data", "")),
            )
            send_json(handler, 201, result)
            return
        if rest == ["templates", "deploy"]:
            template_id = str(
                payload.get("template")
                or payload.get("templateId")
                or payload.get("id")
                or ""
            )
            result = template_bundles.deploy(
                template_id,
                overwrite=bool(payload.get("overwrite")),
                expected_shas=(
                    payload.get("expected_shas")
                    if isinstance(payload.get("expected_shas"), dict)
                    else None
                ),
                project=self._project(payload, query),
            )
            send_json(handler, 200, result)
            return
        if rest == ["templates"]:
            result = workspace.create_template(
                str(payload.get("name", "")),
                str(payload.get("code", "")),
            )
            send_json(handler, 201, {"template": result})
            return
        if rest == ["code", "propose"]:
            path = ensure_editable_path(str(payload.get("path", "escenas/main.py")))
            raw_context = payload.get("context")
            if not isinstance(raw_context, dict):
                raw_context = {}
            built_context = context_builder.build_context(
                path,
                str(raw_context.get("mode") or "buffer"),
                raw_context.get("paths"),
            )
            result = propose_code_change(
                str(payload.get("message", "")),
                path,
                str(payload.get("code", "")),
                provider=self.llm,
                history=payload.get("history") if isinstance(payload.get("history"), list) else [],
                context_files=built_context["files"],
            )
            result["context"] = {
                "mode": built_context["mode"],
                "files": [item["path"] for item in built_context["files"]],
                "chars": built_context["chars"],
                "omitted": built_context["omitted"],
                "truncated": built_context["truncated"],
            }
            send_json(handler, 200, result)
            return
        if rest == ["code", "apply"]:
            path = ensure_editable_path(str(payload.get("path", "")))
            result = workspace.write(
                path,
                str(payload.get("code", "")),
                payload.get("sha256"),
            )
            send_json(handler, 200, result)
            return
        raise ApiError(404, "Ruta de espacio de trabajo no encontrada.")
