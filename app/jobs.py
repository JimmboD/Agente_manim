"""Gestor de jobs de render.

Cada render corre en un subproceso aislado con su propio directorio de medios.
El gestor permite un job activo por escena, cancela el anterior y transmite
logs por SSE.
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
from collections import deque
from pathlib import Path

from app.config import BASE_DIR, EDITOR_MEDIA_DIR, MEDIA_DIR
from app.db import Database


class JobError(RuntimeError):
    pass


def _python_executable() -> str:
    venv_python = BASE_DIR / ".venv" / "Scripts" / "python.exe"
    if venv_python.is_file():
        return str(venv_python)
    return sys.executable


def _popen_kwargs() -> dict:
    if os.name == "nt":
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    return {"start_new_session": True}


def _kill_tree(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                capture_output=True,
                text=True,
                timeout=15,
            )
        else:
            os.killpg(os.getpgid(process.pid), 15)
    except Exception:
        try:
            process.kill()
        except Exception:
            pass


def _find_video(job_dir: Path) -> Path | None:
    candidates = [
        path for path in job_dir.rglob("*.mp4")
        if "partial_movie_files" not in path.as_posix()
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


class JobManager:
    def __init__(self, db: Database, broadcast=None):
        self.db = db
        self.broadcast = broadcast or (lambda *args, **kwargs: None)
        self._lock = threading.RLock()
        self._procs: dict[str, subprocess.Popen] = {}
        self._logs: dict[str, deque[str]] = {}
        self._active_by_scene: dict[str, str] = {}
        self._cancelled: set[str] = set()

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def submit(
        self,
        scene_id: str,
        code: str,
        *,
        format_id: str,
        quality: str,
        replace: bool = True,
    ) -> dict:
        if replace:
            self.cancel_scene(scene_id, reason="reemplazado por un render nuevo")

        render = self.db.create_render(scene_id, format_id=format_id, quality=quality)
        job_id = render["id"]
        job_dir = EDITOR_MEDIA_DIR / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        scene_path = job_dir / "scene.py"
        scene_path.write_text(code, encoding="utf-8")

        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONPATH"] = str(BASE_DIR) + os.pathsep + env.get("PYTHONPATH", "")
        env["MANIM_STUDIO_HEADLESS"] = "1"
        env["MANIM_QUALITY"] = quality
        env["MANIM_FORMAT"] = format_id
        env["MANIM_MEDIA_DIR"] = str(job_dir)

        self._logs[job_id] = deque(maxlen=4000)
        with self._lock:
            # Conserva solo los logs de los últimos 100 jobs.
            for stale in list(self._logs)[:-100]:
                self._logs.pop(stale, None)
        self._log(job_id, f"> Ejecutando escena {scene_id} ({format_id}, {quality})")

        try:
            process = subprocess.Popen(
                [_python_executable(), "-u", str(scene_path)],
                cwd=str(BASE_DIR),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding="utf-8",
                errors="replace",
                **_popen_kwargs(),
            )
        except Exception as exc:
            self.db.update_render(
                job_id,
                status="error",
                error=str(exc),
                finished_at=time.time(),
            )
            raise JobError(f"No se pudo iniciar el render: {exc}") from exc

        with self._lock:
            self._procs[job_id] = process
            self._active_by_scene[scene_id] = job_id

        self.db.update_render(
            job_id,
            status="running",
            started_at=time.time(),
        )
        self.broadcast("editor.job", {"job_id": job_id, "status": "running", "scene_id": scene_id})

        thread = threading.Thread(
            target=self._consume,
            args=(job_id, scene_id, job_dir, process),
            daemon=True,
            name=f"render-{job_id[:8]}",
        )
        thread.start()
        return self.get(job_id) or render

    def get(self, job_id: str) -> dict | None:
        render = self.db.get_render(job_id)
        if not render:
            return None
        with self._lock:
            logs = list(self._logs.get(job_id, ()))
        render["logs"] = logs[-300:]
        return render

    def cancel(self, job_id: str, reason: str = "cancelado por el usuario") -> dict | None:
        render = self.db.get_render(job_id)
        if not render:
            return None
        if render["status"] not in {"queued", "running"}:
            return render

        with self._lock:
            process = self._procs.get(job_id)
            self._cancelled.add(job_id)

        if process and process.poll() is None:
            _kill_tree(process)
            try:
                process.wait(timeout=5)
            except Exception:
                pass

        self._log(job_id, f"> {reason}")
        updated = self.db.update_render(
            job_id,
            status="cancelled",
            error=reason,
            finished_at=time.time(),
        )
        self.broadcast("editor.job", {"job_id": job_id, "status": "cancelled"})
        return updated

    def cancel_scene(self, scene_id: str, reason: str = "reemplazado") -> None:
        with self._lock:
            job_id = self._active_by_scene.get(scene_id)
        if job_id:
            self.cancel(job_id, reason=reason)

    def active_for_scene(self, scene_id: str) -> str | None:
        with self._lock:
            job_id = self._active_by_scene.get(scene_id)
        if not job_id:
            return None
        render = self.db.get_render(job_id)
        if render and render["status"] in {"queued", "running"}:
            return job_id
        return None

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------
    def _log(self, job_id: str, line: str, level: str = "info") -> None:
        with self._lock:
            if job_id not in self._logs:
                self._logs[job_id] = deque(maxlen=4000)
            self._logs[job_id].append(line)
        self.broadcast(
            "editor.job.log",
            {"job_id": job_id, "line": line, "level": level},
        )

    def _classify(self, line: str) -> str:
        upper = line.upper()
        if "TRACEBACK" in upper or "ERROR" in upper or "EXCEPTION" in upper:
            return "error"
        if "WARNING" in upper:
            return "warning"
        if "ANIMATION" in upper or "PLAYED" in upper:
            return "progress"
        return "info"

    def _consume(
        self,
        job_id: str,
        scene_id: str,
        job_dir: Path,
        process: subprocess.Popen,
    ) -> None:
        try:
            assert process.stdout is not None
            for raw_line in process.stdout:
                line = raw_line.rstrip("\r\n")
                if line:
                    self._log(job_id, line, self._classify(line))

            process.wait()
            returncode = process.returncode
            render = self.db.get_render(job_id) or {}
            started_at = render.get("started_at") or time.time()
            duration = time.time() - started_at

            with self._lock:
                cancelled = job_id in self._cancelled
                self._cancelled.discard(job_id)

            if cancelled:
                self.db.update_render(
                    job_id,
                    status="cancelled",
                    finished_at=time.time(),
                )
                self.broadcast("editor.job", {"job_id": job_id, "status": "cancelled"})
                return

            if returncode != 0:
                message = f"El render falló con código {returncode}."
                self._log(job_id, f"✗ {message}", "error")
                self.db.update_render(
                    job_id,
                    status="error",
                    error=message,
                    finished_at=time.time(),
                )
                self.broadcast(
                    "editor.job",
                    {"job_id": job_id, "status": "error", "error": message},
                )
                return

            video = _find_video(job_dir)
            if not video:
                message = "El render terminó pero no se encontró ningún MP4."
                self._log(job_id, f"✗ {message}", "error")
                self.db.update_render(
                    job_id,
                    status="error",
                    error=message,
                    finished_at=time.time(),
                )
                self.broadcast(
                    "editor.job",
                    {"job_id": job_id, "status": "error", "error": message},
                )
                return

            relative = video.relative_to(MEDIA_DIR).as_posix()
            video_url = f"/media/{relative}?t={int(video.stat().st_mtime)}"
            self._log(job_id, f"✓ Render listo en {duration:.1f}s", "success")
            self.db.update_render(
                job_id,
                status="success",
                video_path=str(video),
                video_url=video_url,
                finished_at=time.time(),
            )
            self.broadcast(
                "editor.job",
                {
                    "job_id": job_id,
                    "status": "success",
                    "video_url": video_url,
                    "duration": round(duration, 1),
                },
            )
        except Exception as exc:
            self._log(job_id, f"✗ Error interno del job: {exc}", "error")
            self.db.update_render(
                job_id,
                status="error",
                error=str(exc),
                finished_at=time.time(),
            )
            self.broadcast(
                "editor.job",
                {"job_id": job_id, "status": "error", "error": str(exc)},
            )
        finally:
            with self._lock:
                self._procs.pop(job_id, None)
                if self._active_by_scene.get(scene_id) == job_id:
                    self._active_by_scene.pop(scene_id, None)
