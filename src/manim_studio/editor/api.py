"""Adaptador HTTP del editor.

`manim_studio.servidor` es el servidor; este módulo contiene las rutas nuevas
bajo `/api/editor/*` y no depende de `BaseHTTPRequestHandler` más allá de
enviar la respuesta.
"""

from __future__ import annotations

import json
import traceback
import uuid
from typing import Any

from manim_studio.editor.codegen import code_diff, generate_code, validate_generated_code
from manim_studio.editor.config import DEFAULT_QUALITY, FORMATS, QUALITIES
from manim_studio.editor.db import Database
from manim_studio.editor.ir import (
    IRValidationError,
    default_ir,
    merge_patch,
    normalize_ir,
)
from manim_studio.editor.jobs import JobError, JobManager
from manim_studio.editor.llm import LLMError, LLMProposal, LLMProvider, MockProvider, provider_info
from manim_studio.editor.prompts import summarize_patch


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

        if len(rest) == 3 and rest[0] == "scenes" and rest[2] == "chat":
            scene = self.db.get_scene(rest[1])
            if not scene:
                raise ApiError(404, "Escena no encontrada.")
            _send_json(
                handler,
                200,
                {"messages": self.db.list_chat_messages(scene["id"])},
            )
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

        if len(rest) == 3 and rest[0] == "scenes" and rest[2] == "apply":
            scene = self._require_scene(rest[1])
            result = self._apply(scene, payload)
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
            "llm": provider_info(self.llm),
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

    # ------------------------------------------------------------------
    # Asistente: proponer / aplicar
    # ------------------------------------------------------------------
    def _history(self, scene_id: str) -> list[dict]:
        return [
            {"role": item["role"], "content": item["content"]}
            for item in self.db.list_chat_messages(scene_id, limit=6)
        ]

    def _last_render_error(self, scene_id: str) -> str | None:
        for render in self.db.list_renders(scene_id, limit=5):
            if render.get("error"):
                return str(render["error"])
        return None

    def _propose(self, message: str, scene: dict, payload: dict):
        context = {
            "scene_id": scene["id"],
            "history": self._history(scene["id"]),
            "last_error": self._last_render_error(scene["id"]),
            "focus": payload.get("focus"),
        }
        try:
            return self.llm.propose(message, scene["ir"], context=context), context, None
        except LLMError as exc:
            fallback = f"(Proveedor LLM no disponible: usé respuestas locales: {exc})"
            return MockProvider().propose(message, scene["ir"], context=context), context, fallback

    def _validate_proposal(
        self,
        proposal: LLMProposal,
        scene: dict,
        message: str,
        context: dict,
    ) -> tuple[dict | None, str | None, dict | None, str | None]:
        """Devuelve (IR, código, parche efectivo, error). Nada se guarda aquí."""

        try:
            new_ir = merge_patch(scene["ir"], proposal.patch) if proposal.patch else scene["ir"]
            new_code = generate_code(new_ir)
            validate_generated_code(new_code)
            return new_ir, new_code, proposal.patch, None
        except (IRValidationError, ValueError) as exc:
            error = str(exc)

        repair = getattr(self.llm, "repair", None)
        if repair and proposal.patch:
            try:
                repaired = repair(proposal, error, message, scene["ir"], context)
                new_ir = merge_patch(scene["ir"], repaired.patch) if repaired.patch else scene["ir"]
                new_code = generate_code(new_ir)
                validate_generated_code(new_code)
                return new_ir, new_code, repaired.patch, None
            except Exception as exc:  # el reintento nunca debe tumbar la petición
                error = f"{error} Reintento: {exc}"

        return None, None, None, error

    def _chat(self, scene: dict, payload: dict) -> dict:
        """Pide una propuesta. No guarda cambios ni lanza renders."""

        message = str(payload.get("message", "")).strip()
        if not message:
            raise ApiError(400, "Escribe un mensaje para el asistente.")

        proposal, context, fallback = self._propose(message, scene, payload)
        new_ir, new_code, effective_patch, error = self._validate_proposal(
            proposal, scene, message, context
        )

        if error:
            reply = f"No pude preparar ese cambio: {error}"
            self.db.add_chat_message(scene["id"], role="user", content=message)
            self.db.add_chat_message(scene["id"], role="assistant", content=reply)
            return {
                "reply": reply,
                "error": error,
                "summary": [],
                "patch": {},
                "proposal_id": uuid.uuid4().hex,
                "base_revision": scene["revision"],
                "ir": scene["ir"],
                "code": scene["code"],
                "code_diff": "",
                "scene": self._scene_payload(scene),
                "job": None,
                "llm": provider_info(self.llm),
            }

        if fallback:
            proposal.reply = f"{proposal.reply} {fallback}"
        summary = proposal.summary or summarize_patch(effective_patch)
        self.db.add_chat_message(scene["id"], role="user", content=message)
        self.db.add_chat_message(
            scene["id"],
            role="assistant",
            content=proposal.reply,
            patch=effective_patch,
            summary=summary,
        )

        return {
            "reply": proposal.reply,
            "summary": summary,
            "patch": effective_patch,
            "proposal_id": uuid.uuid4().hex,
            "base_revision": scene["revision"],
            "ir": new_ir,
            "code": new_code,
            "code_diff": code_diff(scene["code"], new_code),
            "scene": self._scene_payload(scene),
            "job": None,
            "llm": provider_info(self.llm),
        }

    def _apply(self, scene: dict, payload: dict) -> dict:
        """Aplica un parche revisado, con control optimista de revisión."""

        try:
            base_revision = int(payload.get("base_revision", scene["revision"]))
        except (TypeError, ValueError) as exc:
            raise ApiError(400, "base_revision debe ser un entero.") from exc

        current = self.db.get_scene(scene["id"]) or scene
        if int(current["revision"]) != base_revision:
            raise ApiError(
                409,
                "La escena cambió mientras revisabas la propuesta. Vuelve a pedir el cambio.",
            )

        patch = payload.get("patch")
        if payload.get("ir") is not None:
            # Camino usado por «Deshacer»: se envía el IR anterior completo.
            patch = {}
            try:
                new_ir = normalize_ir(payload["ir"])
            except IRValidationError as exc:
                raise ApiError(422, str(exc)) from exc
        else:
            if not isinstance(patch, dict):
                raise ApiError(400, "No hay parche para aplicar.")
            try:
                new_ir = merge_patch(current["ir"], patch)
            except IRValidationError as exc:
                raise ApiError(422, str(exc)) from exc

        new_code = generate_code(new_ir)
        validate_generated_code(new_code)

        self.jobs.cancel_scene(scene["id"], reason="escena actualizada por el asistente")
        updated = self.db.update_scene(
            scene["id"],
            title=new_ir["title"],
            ir=new_ir,
            code=new_code,
            expected_revision=base_revision,
        )
        if not updated:
            raise ApiError(409, "La escena cambió mientras se aplicaba el cambio.")

        job = None
        if bool(payload.get("render", True)):
            job = self.jobs.submit(
                updated["id"],
                updated["code"],
                format_id=new_ir["format"],
                quality=str(payload.get("quality") or DEFAULT_QUALITY),
            )

        return {
            "scene": self._scene_payload(updated),
            "job": job,
            "code_diff": code_diff(current["code"], new_code),
            "patch": patch,
            "summary": summarize_patch(patch),
        }
