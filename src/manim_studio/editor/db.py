"""Persistencia SQLite del editor.

Un único archivo (`var/data/editor.db`) con proyectos, escenas, renders y assets.
La conexión se comparte entre hilos con un lock; el volumen es local y bajo.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS projects (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    created_at  REAL NOT NULL,
    updated_at  REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS scenes (
    id          TEXT PRIMARY KEY,
    project_id  TEXT NOT NULL,
    title       TEXT NOT NULL,
    method      TEXT NOT NULL,
    ir_json     TEXT NOT NULL,
    code        TEXT NOT NULL,
    revision    INTEGER NOT NULL DEFAULT 1,
    created_at  REAL NOT NULL,
    updated_at  REAL NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS renders (
    id          TEXT PRIMARY KEY,
    scene_id    TEXT NOT NULL,
    format      TEXT NOT NULL,
    quality     TEXT NOT NULL,
    status      TEXT NOT NULL,
    video_path  TEXT,
    video_url   TEXT,
    log         TEXT,
    error       TEXT,
    created_at  REAL NOT NULL,
    started_at  REAL,
    finished_at REAL,
    FOREIGN KEY (scene_id) REFERENCES scenes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS assets (
    id          TEXT PRIMARY KEY,
    project_id  TEXT NOT NULL,
    kind        TEXT NOT NULL,
    filename    TEXT NOT NULL,
    path        TEXT NOT NULL,
    created_at  REAL NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id          TEXT PRIMARY KEY,
    scene_id    TEXT NOT NULL,
    role        TEXT NOT NULL,
    content     TEXT NOT NULL,
    patch_json  TEXT,
    summary_json TEXT,
    created_at  REAL NOT NULL,
    FOREIGN KEY (scene_id) REFERENCES scenes(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_scenes_project ON scenes(project_id);
CREATE INDEX IF NOT EXISTS idx_renders_scene ON renders(scene_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_assets_project ON assets(project_id);
CREATE INDEX IF NOT EXISTS idx_chat_scene ON chat_messages(scene_id, created_at);
"""


def _now() -> float:
    return time.time()


def _new_id() -> str:
    return uuid.uuid4().hex


class Database:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.executescript(SCHEMA)
            columns = {row["name"] for row in self._conn.execute("PRAGMA table_info(scenes)")}
            if "revision" not in columns:
                self._conn.execute(
                    "ALTER TABLE scenes ADD COLUMN revision INTEGER NOT NULL DEFAULT 1"
                )
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.commit()

    # ------------------------------------------------------------------
    # Proyectos
    # ------------------------------------------------------------------
    def create_project(self, name: str) -> dict:
        project_id = _new_id()
        timestamp = _now()
        clean_name = (name or "Proyecto sin nombre").strip()[:120] or "Proyecto sin nombre"
        with self._lock:
            self._conn.execute(
                "INSERT INTO projects (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (project_id, clean_name, timestamp, timestamp),
            )
            self._conn.commit()
        return {
            "id": project_id,
            "name": clean_name,
            "created_at": timestamp,
            "updated_at": timestamp,
        }

    def list_projects(self) -> list[dict]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM projects ORDER BY updated_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    def get_project(self, project_id: str) -> dict | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM projects WHERE id = ?", (project_id,)
            ).fetchone()
        return dict(row) if row else None

    def touch_project(self, project_id: str) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE projects SET updated_at = ? WHERE id = ?",
                (_now(), project_id),
            )
            self._conn.commit()

    # ------------------------------------------------------------------
    # Escenas
    # ------------------------------------------------------------------
    def create_scene(
        self,
        project_id: str,
        *,
        title: str,
        method: str,
        ir: dict,
        code: str,
    ) -> dict:
        scene_id = _new_id()
        timestamp = _now()
        payload = json.dumps(ir, ensure_ascii=False)
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO scenes
                    (id, project_id, title, method, ir_json, code, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (scene_id, project_id, title[:120], method, payload, code, timestamp, timestamp),
            )
            self._conn.commit()
        self.touch_project(project_id)
        return {
            "id": scene_id,
            "project_id": project_id,
            "title": title[:120],
            "method": method,
            "ir": ir,
            "code": code,
            "revision": 1,
            "created_at": timestamp,
            "updated_at": timestamp,
        }

    def _scene_row(self, row: sqlite3.Row) -> dict:
        data = dict(row)
        data["ir"] = json.loads(data.pop("ir_json"))
        return data

    def get_scene(self, scene_id: str) -> dict | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM scenes WHERE id = ?", (scene_id,)
            ).fetchone()
        return self._scene_row(row) if row else None

    def list_scenes(self, project_id: str) -> list[dict]:
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT id, project_id, title, method, ir_json, revision, created_at, updated_at
                FROM scenes WHERE project_id = ?
                ORDER BY updated_at DESC
                """,
                (project_id,),
            ).fetchall()
        scenes = []
        for row in rows:
            item = dict(row)
            ir = json.loads(item.pop("ir_json"))
            item["format"] = ir.get("format", "16:9")
            item["method"] = ir.get("method", item.get("method", "biseccion"))
            scenes.append(item)
        return scenes

    def update_scene(
        self,
        scene_id: str,
        *,
        title: str | None = None,
        ir: dict | None = None,
        code: str | None = None,
        expected_revision: int | None = None,
    ) -> dict | None:
        """Actualiza una escena y sube su revisión.

        Si se indica `expected_revision`, un desajuste devuelve `None` sin
        escribir: es el control optimista usado por `POST .../apply`.
        """

        current = self.get_scene(scene_id)
        if not current:
            return None
        if expected_revision is not None and int(current["revision"]) != int(expected_revision):
            return None

        new_title = (title if title is not None else current["title"])[:120]
        new_ir = ir if ir is not None else current["ir"]
        new_code = code if code is not None else current["code"]
        timestamp = _now()
        new_revision = int(current["revision"]) + 1

        with self._lock:
            cursor = self._conn.execute(
                """
                UPDATE scenes
                SET title = ?, method = ?, ir_json = ?, code = ?, revision = ?, updated_at = ?
                WHERE id = ? AND revision = ?
                """,
                (
                    new_title,
                    new_ir.get("method", current["method"]),
                    json.dumps(new_ir, ensure_ascii=False),
                    new_code,
                    new_revision,
                    timestamp,
                    scene_id,
                    current["revision"],
                ),
            )
            self._conn.commit()
            if cursor.rowcount == 0:
                return None

        self.touch_project(current["project_id"])
        return self.get_scene(scene_id)

    # ------------------------------------------------------------------
    # Chat
    # ------------------------------------------------------------------
    def add_chat_message(
        self,
        scene_id: str,
        *,
        role: str,
        content: str,
        patch: dict | None = None,
        summary: list[str] | None = None,
    ) -> dict:
        message_id = _new_id()
        timestamp = _now()
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO chat_messages
                    (id, scene_id, role, content, patch_json, summary_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message_id,
                    scene_id,
                    role,
                    str(content)[:4000],
                    json.dumps(patch, ensure_ascii=False) if patch is not None else None,
                    json.dumps(summary, ensure_ascii=False) if summary is not None else None,
                    timestamp,
                ),
            )
            self._conn.commit()
        return {
            "id": message_id,
            "scene_id": scene_id,
            "role": role,
            "content": str(content)[:4000],
            "patch": patch,
            "summary": summary or [],
            "created_at": timestamp,
        }

    def list_chat_messages(self, scene_id: str, limit: int = 50) -> list[dict]:
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT * FROM chat_messages
                WHERE scene_id = ?
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (scene_id, max(1, min(limit, 200))),
            ).fetchall()
        messages = []
        for row in rows:
            item = dict(row)
            item["patch"] = json.loads(item["patch_json"]) if item["patch_json"] else None
            item["summary"] = json.loads(item["summary_json"]) if item["summary_json"] else []
            item.pop("patch_json", None)
            item.pop("summary_json", None)
            messages.append(item)
        return messages

    # ------------------------------------------------------------------
    # Renders
    # ------------------------------------------------------------------
    def create_render(self, scene_id: str, *, format_id: str, quality: str) -> dict:
        render_id = _new_id()
        timestamp = _now()
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO renders
                    (id, scene_id, format, quality, status, created_at)
                VALUES (?, ?, ?, ?, 'queued', ?)
                """,
                (render_id, scene_id, format_id, quality, timestamp),
            )
            self._conn.commit()
        return {
            "id": render_id,
            "scene_id": scene_id,
            "format": format_id,
            "quality": quality,
            "status": "queued",
            "video_path": None,
            "video_url": None,
            "log": "",
            "error": None,
            "created_at": timestamp,
            "started_at": None,
            "finished_at": None,
        }

    def update_render(self, render_id: str, **fields: Any) -> dict | None:
        allowed = {
            "status", "video_path", "video_url", "log", "error",
            "started_at", "finished_at",
        }
        updates = {key: value for key, value in fields.items() if key in allowed}
        if not updates:
            return self.get_render(render_id)

        assignments = ", ".join(f"{key} = ?" for key in updates)
        values = list(updates.values()) + [render_id]
        with self._lock:
            self._conn.execute(
                f"UPDATE renders SET {assignments} WHERE id = ?", values
            )
            self._conn.commit()
        return self.get_render(render_id)

    def get_render(self, render_id: str) -> dict | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM renders WHERE id = ?", (render_id,)
            ).fetchone()
        return dict(row) if row else None

    def list_renders(self, scene_id: str, limit: int = 10) -> list[dict]:
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT * FROM renders
                WHERE scene_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (scene_id, max(1, min(limit, 50))),
            ).fetchall()
        return [dict(row) for row in rows]

    def latest_render(self, scene_id: str, format_id: str | None = None) -> dict | None:
        if format_id:
            with self._lock:
                row = self._conn.execute(
                    """
                    SELECT * FROM renders
                    WHERE scene_id = ? AND format = ? AND status = 'success'
                    ORDER BY created_at DESC LIMIT 1
                    """,
                    (scene_id, format_id),
                ).fetchone()
        else:
            with self._lock:
                row = self._conn.execute(
                    """
                    SELECT * FROM renders
                    WHERE scene_id = ? AND status = 'success'
                    ORDER BY created_at DESC LIMIT 1
                    """,
                    (scene_id,),
                ).fetchone()
        return dict(row) if row else None

    # ------------------------------------------------------------------
    # Assets
    # ------------------------------------------------------------------
    def create_asset(
        self,
        project_id: str,
        *,
        kind: str,
        filename: str,
        path: str,
    ) -> dict:
        asset_id = _new_id()
        timestamp = _now()
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO assets (id, project_id, kind, filename, path, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (asset_id, project_id, kind, filename, path, timestamp),
            )
            self._conn.commit()
        return {
            "id": asset_id,
            "project_id": project_id,
            "kind": kind,
            "filename": filename,
            "path": path,
            "created_at": timestamp,
        }

    def list_assets(self, project_id: str) -> list[dict]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM assets WHERE project_id = ? ORDER BY created_at DESC",
                (project_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def close(self) -> None:
        with self._lock:
            self._conn.close()
