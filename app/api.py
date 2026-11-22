"""Adaptador HTTP del editor.

`server.py` sigue siendo el servidor; este módulo contiene las rutas nuevas
bajo `/api/editor/*` y no depende de `BaseHTTPRequestHandler` más allá de
enviar la respuesta.
"""

from __future__ import annotations

import json
import traceback
from typing import Any

from app.codegen import code_diff, generate_code, validate_generated_code
from app.config import DEFAULT_QUALITY, FORMATS, QUALITIES
from app.db import Database
from app.ir import (
    IRValidationError,
    default_ir,
    merge_patch,
    normalize_ir,
)
from app.jobs import JobError, JobManager
from app.llm import LLMProvider


class ApiError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def _send_json(handler, status: int, payload: dict) -> None:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.send_cors_headers()
    handler.end_headers()
    handler.wfile.write(data)


def _read_json(body: bytes) -> dict:
    if not body:
        return {}
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ApiError(400, f"JSON inválido: {exc}") from exc
    if not isinstance(payload, dict):
        raise ApiError(400, "El cuerpo debe ser un objeto JSON.")
    return payload


class EditorAPI:
    def __init__(self, db: Database, jobs: JobManager, llm: LLMProvider, token: str | None = None):
        self.db = db
        self.jobs = jobs
        self.llm = llm
        self.token = token

    # ------------------------------------------------------------------
    # Entrada
    # ------------------------------------------------------------------
    def handle(self, handler, method: str, path: str, query: dict, body: bytes) -> bool:
        segments = [segment for segment in path.split("/") if segment]
        if len(segments) < 2 or segments[0] != "api" or segments[1] != "editor":
            return False

        rest = segments[2:]
        try:
            payload = _read_json(body) if method in {"POST", "PUT"} else {}
            if method == "GET":
                self._route_get(handler, rest, query)
            elif method == "POST":
                self._route_post(handler, rest, payload)
            elif method == "PUT":
                self._route_put(handler, rest, payload)
            else:
                raise ApiError(405, f"Método no soportado: {method}")
        except ApiError as exc:
            _send_json(handler, exc.status, {"error": exc.message})
        except IRValidationError as exc:
            _send_json(handler, 422, {"error": str(exc)})
        except JobError as exc:
            _send_json(handler, 500, {"error": str(exc)})
        except Exception as exc:
            traceback.print_exc()
            _send_json(handler, 500, {"error": f"Error interno: {exc}"})
        return True

    # ------------------------------------------------------------------
    # GET
    # ------------------------------------------------------------------
    def _route_get(self, handler, rest: list[str], query: dict) -> None:
        if rest == ["bootstrap"]:
            _send_json(handler, 200, self._bootstrap())
            return

        if rest == ["projects"]:
            _send_json(handler, 200, {"projects": self.db.list_projects()})
            return

        if len(rest) == 2 and rest[0] == "projects":
            project = self.db.get_project(rest[1])
            if not project:
                raise ApiError(404, "Proyecto no encontrado.")
            _send_json(
                handler,
                200,
                {"project": project, "scenes": self.db.list_scenes(project["id"])},
            )
            return

        if len(rest) == 2 and rest[0] == "scenes":
            scene = self.db.get_scene(rest[1])
            if not scene:
                raise ApiError(404, "Escena no encontrada.")
            _send_json(handler, 200, self._scene_payload(scene))
            return

        if len(rest) == 3 and rest[0] == "scenes" and rest[2] == "renders":
            scene = self.db.get_scene(rest[1])
            if not scene:
                raise ApiError(404, "Escena no encontrada.")
            _send_json(handler, 200, {"renders": self.db.list_renders(scene["id"])})
            return

        if len(rest) == 2 and rest[0] == "jobs":
            job = self.jobs.get(rest[1])
            if not job:
                raise ApiError(404, "Job no encontrado.")
            _send_json(handler, 200, {"job": job})
            return

        raise ApiError(404, "Ruta de editor no encontrada.")

    # ------------------------------------------------------------------
    # POST
    # ------------------------------------------------------------------
    def _route_post(self, handler, rest: list[str], payload: dict) -> None:
        if rest == ["projects"]:
            project = self.db.create_project(str(payload.get("name", "Mi proyecto")))
            scene = self._create_default_scene(project["id"])
            _send_json(handler, 201, {"project": project, "scene": scene})
            return

        if len(rest) == 3 and rest[0] == "projects" and rest[2] == "scenes":
            project = self.db.get_project(rest[1])
            if not project:
                raise ApiError(404, "Proyecto no encontrado.")
            scene = self._create_scene(
                project["id"],
                payload.get("ir") or default_ir("biseccion"),
                title=payload.get("title"),
            )
            _send_json(handler, 201, {"scene": scene})
            return

        if len(rest) == 3 and rest[0] == "scenes" and rest[2] == "render":
            scene = self._require_scene(rest[1])
            job = self._submit_render(scene, payload)
            _send_json(handler, 202, {"job": job})
            return

        if len(rest) == 3 and rest[0] == "scenes" and rest[2] == "chat":
            scene = self._require_scene(rest[1])
            result = self._chat(scene, payload)
            _send_json(handler, 200, result)
            return

        if len(rest) == 3 and rest[0] == "jobs" and rest[2] == "cancel":
            job = self.jobs.cancel(rest[1], reason="cancelado desde el editor")
            if not job:
                raise ApiError(404, "Job no encontrado.")
            _send_json(handler, 200, {"job": job})
            return

        raise ApiError(404, "Ruta de editor no encontrada.")

    # ------------------------------------------------------------------
    # PUT
    # ------------------------------------------------------------------
    def _route_put(self, handler, rest: list[str], payload: dict) -> None:
        if len(rest) == 2 and rest[0] == "scenes":
            scene = self._require_scene(rest[1])
            updated = self._save_ir(
                scene,
                payload.get("ir", scene["ir"]),
                title=payload.get("title"),
            )
            _send_json(handler, 200, self._scene_payload(updated))
            return

        raise ApiError(404, "Ruta de editor no encontrada.")

    # ------------------------------------------------------------------
    # Casos de uso
    # ------------------------------------------------------------------
    def _bootstrap(self) -> dict:
        projects = self.db.list_projects()
        if not projects:
            project = self.db.create_project("Mi primer proyecto")
            self._create_default_scene(project["id"])
            projects = [project]

        return {
            "projects": projects,
            "token": self.token,
            "formats": [
                {"id": key, **value} for key, value in FORMATS.items()
            ],
            "qualities": [
                {"id": key, **value} for key, value in QUALITIES.items()
            ],
            "default_ir": default_ir("biseccion"),
            "default_format": "16:9",
            "default_quality": DEFAULT_QUALITY,
            "llm": {"provider": self.llm.name, "mock": self.llm.name == "mock"},
        }

    def _create_default_scene(self, project_id: str) -> dict:
        return self._create_scene(project_id, default_ir("biseccion"))

    def _create_scene(self, project_id: str, ir: dict, title: str | None = None) -> dict:
        normalized = normalize_ir(ir)
        code = generate_code(normalized)
        validate_generated_code(code)
        return self.db.create_scene(
            project_id,
            title=title or normalized["title"],
            method=normalized["method"],
            ir=normalized,
            code=code,
        )

    def _require_scene(self, scene_id: str) -> dict:
        scene = self.db.get_scene(scene_id)
        if not scene:
            raise ApiError(404, "Escena no encontrada.")
        return scene

    def _save_ir(self, scene: dict, ir: dict, title: str | None = None) -> dict:
        normalized = normalize_ir(ir)
        code = generate_code(normalized)
        validate_generated_code(code)
        # Un render en curso quedaría obsoleto: se cancela antes de guardar.
        self.jobs.cancel_scene(scene["id"], reason="escena actualizada")
        updated = self.db.update_scene(
            scene["id"],
            title=title or normalized["title"],
            ir=normalized,
            code=code,
        )
        if not updated:
            raise ApiError(404, "Escena no encontrada.")
        return updated

    def _scene_payload(self, scene: dict) -> dict:
        format_id = scene["ir"].get("format", "16:9")
        return {
            **scene,
            "latest_render": self.db.latest_render(scene["id"], format_id),
            "active_job": self.jobs.active_for_scene(scene["id"]),
        }

    def _submit_render(self, scene: dict, payload: dict) -> dict:
        format_id = str(payload.get("format") or scene["ir"].get("format", "16:9"))
        quality = str(payload.get("quality") or DEFAULT_QUALITY)

        if format_id not in FORMATS:
            raise ApiError(400, f"Formato no soportado: {format_id}")
        if quality not in QUALITIES:
            raise ApiError(400, f"Calidad no soportada: {quality}")

        if format_id != scene["ir"].get("format"):
            scene = self._save_ir(scene, {**scene["ir"], "format": format_id})

        # Un nuevo render de la misma escena reemplaza al anterior: evita
        # subprocesos Manim concurrentes escribiendo código/estado a la vez.
        self.jobs.cancel_scene(scene["id"], reason="reemplazado por un render más reciente")

        return self.jobs.submit(
            scene["id"],
            scene["code"],
            format_id=format_id,
            quality=quality,
        )

    def _chat(self, scene: dict, payload: dict) -> dict:
        message = str(payload.get("message", "")).strip()
        if not message:
            raise ApiError(400, "Escribe un mensaje para el asistente.")

        proposal = self.llm.propose(
            message,
            scene["ir"],
            context={"scene_id": scene["id"]},
        )

        old_code = scene["code"]
        new_ir = merge_patch(scene["ir"], proposal.patch) if proposal.patch else scene["ir"]
        new_code = generate_code(new_ir)
        validate_generated_code(new_code)

        if proposal.patch:
            self.jobs.cancel_scene(scene["id"], reason="escena actualizada por el asistente")

        updated = self.db.update_scene(
            scene["id"],
            title=new_ir["title"],
            ir=new_ir,
            code=new_code,
        )
        diff = code_diff(old_code, new_code)

        job = None
        if proposal.patch and bool(payload.get("auto_render", True)):
            job = self.jobs.submit(
                updated["id"],
                updated["code"],
                format_id=new_ir["format"],
                quality=str(payload.get("quality") or DEFAULT_QUALITY),
            )

        return {
            "reply": proposal.reply,
            "patch": proposal.patch,
            "ir": new_ir,
            "code": new_code,
            "code_diff": diff,
            "scene": self._scene_payload(updated),
            "job": job,
        }
