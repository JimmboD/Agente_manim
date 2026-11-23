import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import json
import hashlib
import time
import glob
import subprocess
import threading
import queue
import mimetypes
import importlib.util
import random
from urllib.parse import urlparse, parse_qs
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path

from manim_studio import PAQUETE_DIR, ROOT
from manim_studio.control import detener_render, solicitar_apagado
from manim_studio.editor.api import EditorAPI
from manim_studio.editor.config import (
    ALLOWED_AUDIO_EXTENSIONS,
    AUDIO_DIR,
    DB_PATH,
    MAIN_PY_PATH,
    MAX_UPLOAD_BYTES,
    MEDIA_DIR,
    PASOS_ALGEBRAICOS_PATH,
    REFERENCIA_TECNICA_PATH,
    TOKEN_PATH,
    WEB_DIR,
    ensure_directories,
)
from manim_studio.editor import projects, workspace
from manim_studio.editor.db import Database
from manim_studio.editor.jobs import JobManager
from manim_studio.editor.llm import get_provider
from manim_studio.editor.security import (
    UnsafePathError,
    allowed_origins,
    ensure_token,
    origin_is_allowed,
    safe_join,
    token_matches,
)
from manim_studio.editor.workspace_api import WorkspaceAPI

# Rutas canónicas: el servidor trabaja con `str` por la API de http.server.
BASE_DIR = str(ROOT)
WEB_DIR = str(WEB_DIR)
MEDIA_DIR = str(MEDIA_DIR)
AUDIO_DIR = str(AUDIO_DIR)
MAIN_PY_PATH = str(MAIN_PY_PATH)
PASOS_ALGEBRAICOS_PATH = str(PASOS_ALGEBRAICOS_PATH)
MOTOR_DIR = PAQUETE_DIR / "motor"
PLANTILLAS_DIR = str(MOTOR_DIR / "plantillas")
GENERADOR_EJERCICIOS_PATH = str(MOTOR_DIR / "ejercicios" / "analisis_numerico.py")
os.makedirs(AUDIO_DIR, exist_ok=True)


def _plantilla(*partes: str) -> str:
    return str(MOTOR_DIR / "plantillas" / Path(*partes))


TEMPLATE_MAP = {
    "regla_falsa": _plantilla("analisis_numerico", "Regla falsa.py"),
    "biseccion": _plantilla("analisis_numerico", "Bisección.py"),
    "newton_raphson": _plantilla("analisis_numerico", "Newton-Raphson.py"),
    "derivada_limite": _plantilla("calculo_diferencial", "Derivada límite.py"),
    "serie_taylor": _plantilla("calculo_diferencial", "Serie de Taylor.py"),
    "integral": _plantilla("calculo_diferencial", "Integral.py"),
    "curva_polinomica": _plantilla("algebra_geometria", "Curva polinómica.py"),
    "hud_algebra": _plantilla("algebra_geometria", "HUD álgebra.py"),
    # Archivo de trabajo canónico: el runner lo lee desde la raíz del proyecto.
    "pasos_algebraicos": PASOS_ALGEBRAICOS_PATH,
    "serie_fourier": _plantilla("ecuaciones_diferenciales", "Serie de Fourier.py"),
    "purga_ciclo_vida": _plantilla("control_ciclo_vida", "Purga ciclo de vida.py"),
    "simplex": _plantilla("investigacion_operaciones", "Simplex.py"),
}


def _project_slug(query=None, payload=None) -> str:
    """Resuelve el proyecto de una petición sin aceptar slugs inexistentes."""

    candidate = ""
    if payload:
        candidate = str(payload.get("project") or "").strip()
    if not candidate and query:
        candidate = str((query.get("project") or [""])[0] or "").strip()
    available = {item["slug"] for item in projects.list_projects()}
    if candidate in available:
        return candidate
    return projects.active_slug()


def _main_path(slug=None) -> str:
    return str(projects.main_py_path(slug or projects.active_slug()))


def _pasos_path(slug=None) -> str:
    return str(projects.pasos_path(slug or projects.active_slug()))


def resolve_run_target(payload: dict, query: dict | None = None) -> dict:
    """Resuelve de forma estricta qué archivo se debe ejecutar.

    La ruta pública ``path`` es la fuente de verdad. Si no viene, se mantiene
    el comportamiento heredado para llamadas antiguas que sólo envían código.
    """

    format_id = str(payload.get("format") or "16:9")
    if format_id not in ("16:9", "9:16", "1:1"):
        format_id = "16:9"
    quality = str(payload.get("quality") or "low_quality")
    if quality not in ("low_quality", "medium_quality", "high_quality"):
        quality = "low_quality"

    slug = _project_slug(query, payload)
    workspace.set_project(slug)
    rel_path = str(payload.get("path") or "").strip()
    if rel_path:
        candidate, _writable, root_name = workspace.resolve(rel_path)
        if root_name != "escenas" or candidate.suffix.lower() != ".py" or not candidate.is_file():
            raise workspace.WorkspaceError(
                400, "Solo se pueden ejecutar archivos .py de la carpeta Proyecto."
            )
        # El buffer del editor manda: se escribe en la ruta validada justo antes
        # de lanzar el proceso para ejecutar siempre el código que ve el usuario.
        code = payload.get("code")
        if isinstance(code, str):
            candidate.write_bytes(code.encode("utf-8"))
        data = candidate.read_bytes()
        return {
            "slug": slug,
            "path": rel_path,
            "file": candidate.name,
            "script": str(candidate),
            "sha256": hashlib.sha256(data).hexdigest(),
            "size": len(data),
            "format": format_id,
            "quality": quality,
        }

    # Compatibilidad con llamadas que no envían `path` (Short heredado).
    target_file = str(payload.get("file") or "main.py")
    script_path = _main_path(slug)
    if target_file == "pasos_algebraicos.txt":
        with open(_pasos_path(slug), "w", encoding="utf-8") as handle:
            handle.write(str(payload.get("code") or ""))
        runner_code = (
            'from manim_studio.motor.planos.generar_plano import AnimadorGrafico\n\n'
            'if __name__ == "__main__":\n'
            '    escena = AnimadorGrafico()\n'
            '    escena.insertar_algebra("pasos_algebraicos.txt", tiempo_animacion=1.5, tiempo_espera=2.0)\n'
            '    escena.desvanecer_todo(tiempo_animacion=1.5)\n'
            '    escena.render(previsualizar=True)\n'
        )
        with open(script_path, "w", encoding="utf-8") as handle:
            handle.write(runner_code)
    elif isinstance(payload.get("code"), str) and payload["code"].strip():
        with open(script_path, "w", encoding="utf-8") as handle:
            handle.write(payload["code"])
    return {
        "slug": slug,
        "path": None,
        "file": target_file,
        "script": script_path,
        "format": format_id,
        "quality": quality,
    }


# Suscriptores de Server-Sent Events (SSE)
sse_subscribers = []
sse_lock = threading.Lock()

def broadcast_sse(event_type, data):
    msg = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
    with sse_lock:
        dead = []
        for q in sse_subscribers:
            try:
                q.put_nowait(msg)
            except Exception:
                dead.append(q)
        for d in dead:
            if d in sse_subscribers:
                sse_subscribers.remove(d)

def find_latest_video(since=None):
    """Devuelve la URL HTTP del video .mp4 generado más reciente.

    Los archivos viven en ``var/media/`` pero se sirven bajo ``/media/``;
    construir la URL desde la raíz del proyecto dejaría rutas ``/var/...``
    que el servidor no publica.
    """

    newest = find_latest_video_file(since=since)
    if newest:
        rel = os.path.relpath(newest, MEDIA_DIR).replace("\\", "/")
        return f"/media/{rel}?t={int(os.path.getmtime(newest))}"
    return None

def find_latest_video_file(since=None):
    """Retorna la ruta del .mp4 más reciente, opcionalmente posterior a ``since``."""
    video_candidates = glob.glob(os.path.join(MEDIA_DIR, "videos", "**", "*.mp4"), recursive=True)
    video_files = [
        f for f in video_candidates
        if "partial_movie_files" not in f and "exports" not in f
        and (since is None or os.path.getmtime(f) >= since)
    ]
    if video_files:
        return max(video_files, key=os.path.getmtime)
    return None

def terminate_process_tree(proc):
    """Mata el proceso y sus hijos (ffmpeg/Manim pueden dejar huérfanos)."""

    if not proc or proc.poll() is not None:
        return
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                capture_output=True,
                text=True,
                timeout=15,
            )
        else:
            os.killpg(os.getpgid(proc.pid), 15)
        proc.wait(timeout=5)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def get_media_duration(file_path):
    """Obtiene la duración exacta en segundos usando ffprobe."""
    try:
        res = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path],
            capture_output=True, text=True, check=True
        )
        return float(res.stdout.strip())
    except Exception:
        return 0.0

_generador_ejercicios_mod = None

# ---------------------------------------------------------------------------
# Editor de escenas (SQLite + jobs de render + proveedor LLM)
# ---------------------------------------------------------------------------
_editor_lock = threading.Lock()
_editor_api = None
_workspace_api = None
_editor_token = None


def get_editor_token():
    global _editor_token
    if _editor_token is None:
        ensure_directories()
        _editor_token = ensure_token(TOKEN_PATH)
    return _editor_token


def get_editor_api():
    global _editor_api
    if _editor_api is None:
        with _editor_lock:
            if _editor_api is None:
                ensure_directories()
                db = Database(DB_PATH)
                jobs = JobManager(db, broadcast=broadcast_sse)
                _editor_api = EditorAPI(
                    db,
                    jobs,
                    get_provider(),
                    token=get_editor_token(),
                )
    return _editor_api


def get_workspace_api():
    global _workspace_api
    if _workspace_api is None:
        with _editor_lock:
            if _workspace_api is None:
                _workspace_api = WorkspaceAPI(llm=get_editor_api().llm)
    return _workspace_api


def obtener_generador_ejercicios():
    global _generador_ejercicios_mod
    if _generador_ejercicios_mod is None:
        ruta = GENERADOR_EJERCICIOS_PATH
        if not os.path.isfile(ruta):
            raise FileNotFoundError(f"No se encontró el script generador en: {ruta}")
        spec = importlib.util.spec_from_file_location("generador_ejercicios_analisis_num", ruta)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _generador_ejercicios_mod = mod
    return _generador_ejercicios_mod

class ManimStudioHandler(BaseHTTPRequestHandler):
    def handle_random_exercise(self, metodo_param=""):
        try:
            if metodo_param and ("taylor" in metodo_param.lower() or "serie" in metodo_param.lower()):
                import sympy as sp
                x = sp.Symbol('x')
                candidatos_taylor = [
                    sp.sin(x),
                    sp.cos(x),
                    sp.exp(x),
                    sp.exp(-x**2),
                    sp.sin(2*x),
                    sp.cos(2*x),
                    sp.cos(x) - x,
                    x * sp.exp(x),
                    1 / (1 + x**2)
                ]
                f_final = random.choice(candidatos_taylor)
                x0 = float(random.choice([-1.0, 0.0, 1.0]))
                res = {
                    "status": "success",
                    "metodo_id": "serie_taylor",
                    "metodo_nombre": "Serie de Taylor",
                    "funcion": str(f_final),
                    "latex": sp.latex(f_final),
                    "a": -3.0,
                    "b": 3.0,
                    "x0": x0,
                    "x_min": -6.0,
                    "x_max": 6.0,
                    "raiz_objetiva": 0.0,
                    "parametros": f"Centro de expansión x₀: {x0}"
                }
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps(res).encode("utf-8"))
                return

            metodo_gen = None
            if metodo_param:
                m_norm = metodo_param.lower().replace("-", "_").replace(" ", "_")
                if "bisecc" in m_norm:
                    metodo_gen = "Bisección"
                elif "regla" in m_norm or "falsa" in m_norm:
                    metodo_gen = "Regla Falsa"
                elif "newton" in m_norm or "raphson" in m_norm:
                    metodo_gen = "Newton-Raphson"
                else:
                    metodo_gen = None

            mod = obtener_generador_ejercicios()
            ejercicio = mod.generar_ejercicio(metodo_gen)

            m_res = ejercicio["metodo"]
            if "Bisecc" in m_res:
                metodo_id = "biseccion"
            elif "Regla" in m_res:
                metodo_id = "regla_falsa"
            elif "Newton" in m_res:
                metodo_id = "newton_raphson"
            else:
                metodo_id = "biseccion"

            ecuacion_str = str(ejercicio["ecuacion"])
            latex_str = ejercicio.get("latex", "")
            raiz_objetiva = round(float(ejercicio.get("raiz_objetiva", 0.0)), 4)

            if metodo_id in ["biseccion", "regla_falsa"]:
                vals = ejercicio["valores_iniciales"]
                a = round(float(vals[0]), 2)
                b = round(float(vals[1]), 2)
                x0 = round((a + b) / 2.0, 2)
                x_min = round(min(a, b, raiz_objetiva) - 1.5, 1)
                x_max = round(max(a, b, raiz_objetiva) + 1.5, 1)
            else:
                x0 = round(float(ejercicio["valores_iniciales"]), 2)
                a = round(x0 - 1.5, 2)
                b = round(x0 + 1.5, 2)
                x_min = round(min(x0, raiz_objetiva) - 1.5, 1)
                x_max = round(max(x0, raiz_objetiva) + 1.5, 1)

            res = {
                "status": "success",
                "metodo_id": metodo_id,
                "metodo_nombre": m_res,
                "funcion": ecuacion_str,
                "latex": latex_str,
                "a": a,
                "b": b,
                "x0": x0,
                "x_min": x_min,
                "x_max": x_max,
                "raiz_objetiva": raiz_objetiva,
                "parametros": ejercicio.get("parametros", "")
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(res).encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
    def log_message(self, format, *args):
        pass

    def send_cors_headers(self):
        """Solo refleja el Origin si es de confianza (localhost del propio puerto)."""

        origin = self.headers.get("Origin")
        if origin:
            port = self.server.server_address[1]
            if origin_is_allowed(origin, allowed_origins(port)):
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Session-Token")
        self.send_header("Access-Control-Allow-Credentials", "true")

    def origin_is_trusted(self):
        origin = self.headers.get("Origin")
        port = self.server.server_address[1]
        return origin_is_allowed(origin, allowed_origins(port))

    def require_trusted_origin(self):
        if self.origin_is_trusted():
            return True
        self.send_response(403)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Origen no permitido."}).encode("utf-8"))
        return False

    def require_token(self):
        provided = self.headers.get("X-Session-Token")
        if token_matches(get_editor_token(), provided):
            return True
        self.send_response(403)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            json.dumps({
                "error": "Token de sesión ausente o inválido.",
                "hint": "Abre la app en http://127.0.0.1:%d/" % self.server.server_address[1],
            }).encode("utf-8")
        )
        return False

    def do_OPTIONS(self):
        if not self.require_trusted_origin():
            return
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if not self.require_trusted_origin():
            return

        editor = get_editor_api()
        if editor.handle(self, "GET", path, parse_qs(parsed.query), b""):
            return
        if get_workspace_api().handle(self, "GET", path, parse_qs(parsed.query), b""):
            return

        # 1. Eventos SSE para streaming en tiempo real
        if path == "/api/events":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_cors_headers()
            self.end_headers()

            client_queue = queue.Queue(maxsize=10000)
            with sse_lock:
                sse_subscribers.append(client_queue)

            try:
                initial = f"event: connected\ndata: {json.dumps({'message': 'Conectado a Manim Engine SSE'})}\n\n"
                self.wfile.write(initial.encode("utf-8"))
                self.wfile.flush()

                # Enviar video actual si ya existe
                latest_vid = find_latest_video()
                if latest_vid:
                    init_vid = f"event: video\ndata: {json.dumps({'video_url': latest_vid})}\n\n"
                    self.wfile.write(init_vid.encode("utf-8"))
                    self.wfile.flush()

                while True:
                    try:
                        msg = client_queue.get(timeout=25)
                        self.wfile.write(msg.encode("utf-8"))
                        self.wfile.flush()
                    except queue.Empty:
                        self.wfile.write(b": heartbeat\n\n")
                        self.wfile.flush()
            except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError, OSError):
                pass
            finally:
                with sse_lock:
                    if client_queue in sse_subscribers:
                        sse_subscribers.remove(client_queue)
            return

        # 2. Obtener contenido actual de main.py (o pasos_algebraicos.txt)
        if path == "/api/get_main":
            query = parse_qs(parsed.query)
            target_file = query.get("file", ["main.py"])[0]
            slug = _project_slug(query)
            if target_file == "pasos_algebraicos.txt":
                file_path = _pasos_path(slug)
            else:
                file_path = _main_path(slug)

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors_headers()
            self.end_headers()
            code = ""
            if os.path.isfile(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    code = f.read()
            self.wfile.write(json.dumps({"code": code, "path": file_path, "file": target_file}).encode("utf-8"))
            return

        # 2b. Obtener la referencia técnica para la vista de documentación.
        if path == "/api/get_readme":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors_headers()
            self.end_headers()
            readme_path = str(REFERENCIA_TECNICA_PATH)
            readme_content = ""
            if os.path.isfile(readme_path):
                with open(readme_path, "r", encoding="utf-8") as f:
                    readme_content = f.read()
            self.wfile.write(json.dumps({"content": readme_content}).encode("utf-8"))
            return

        # 2c. Obtener plantilla matemática directamente desde el paquete de plantillas
        if path == "/api/get_template":
            query = parse_qs(parsed.query)
            template_id = query.get("id", [""])[0].strip()
            req_file = query.get("file", [""])[0].strip()

            file_path = None
            if template_id == "pasos_algebraicos":
                candidate = _pasos_path(_project_slug(query))
                if os.path.isfile(candidate):
                    file_path = candidate
            if not file_path and template_id in TEMPLATE_MAP:
                candidate = os.path.normpath(TEMPLATE_MAP[template_id])
                if os.path.isfile(candidate):
                    file_path = candidate

            if not file_path and req_file:
                clean_rel = req_file.lstrip("/\\").replace("\\", "/")
                try:
                    candidate = safe_join(PLANTILLAS_DIR, clean_rel)
                except UnsafePathError:
                    candidate = None
                if candidate and os.path.isfile(candidate):
                    file_path = str(candidate)

            if not file_path and template_id:
                clean_id = template_id.lower().replace("-", "_").replace(" ", "_")
                for root, dirs, files in os.walk(PLANTILLAS_DIR):
                    for f in files:
                        f_stem = os.path.splitext(f)[0].lower().replace("-", "_").replace(" ", "_")
                        if f_stem == clean_id:
                            file_path = os.path.join(root, f)
                            break
                    if file_path:
                        break

            if not file_path or not os.path.isfile(file_path):
                self.send_response(404)
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Plantilla '{template_id}' no encontrada en src/manim_studio/motor/plantillas/"}).encode("utf-8"))
                return

            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()

            rel_p = "/" + os.path.relpath(file_path, BASE_DIR).replace("\\", "/")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "code": code,
                "template_id": template_id,
                "filename": os.path.basename(file_path),
                "path": rel_p
            }).encode("utf-8"))
            return

        # 3. Obtener último video generado
        if path == "/api/latest_video":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors_headers()
            self.end_headers()
            vid = find_latest_video()
            self.wfile.write(json.dumps({"video_url": vid}).encode("utf-8"))
            return

        # 3c. Generador de ejercicio aleatorio para Shorts (Ruleta o por método)
        if path == "/api/short/random_exercise":
            query = parse_qs(parsed.query)
            metodo_param = query.get("metodo", [""])[0].strip()
            self.handle_random_exercise(metodo_param)
            return

        # 3b. Obtener lista de audios disponibles en el servidor
        if path == "/api/get_audios":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors_headers()
            self.end_headers()
            audios = []
            if os.path.isdir(AUDIO_DIR):
                for f in sorted(os.listdir(AUDIO_DIR)):
                    fp = os.path.join(AUDIO_DIR, f)
                    if os.path.isfile(fp):
                        audios.append({
                            "name": f,
                            "url": f"/audios/{f}",
                            "size": os.path.getsize(fp),
                            "modified": os.path.getmtime(fp)
                        })
            self.wfile.write(json.dumps({"audios": audios}).encode("utf-8"))
            return

        # 4. Servir archivos multimedia (videos MP4 generados con soporte Range)
        if path.startswith("/media/"):
            rel_path = path[len("/media/"):]
            try:
                full_path = safe_join(MEDIA_DIR, rel_path)
            except UnsafePathError:
                self.send_error(404, "Video no encontrado")
                return
            if full_path.is_file():
                self.serve_file_with_range(str(full_path), "video/mp4")
                return
            else:
                self.send_error(404, "Video no encontrado")
                return

        # 4b. Servir archivos de audio con soporte Range
        if path.startswith("/audios/"):
            rel_path = path[len("/audios/"):]
            try:
                full_path = safe_join(AUDIO_DIR, rel_path)
            except UnsafePathError:
                self.send_error(404, "Audio no encontrado")
                return
            if full_path.is_file():
                mime, _ = mimetypes.guess_type(str(full_path))
                if not mime or not mime.startswith("audio/"):
                    mime = "audio/mpeg"
                self.serve_file_with_range(str(full_path), mime)
                return
            else:
                self.send_error(404, "Audio no encontrado")
                return

        # 5. Servir Frontend estático (HTML, CSS, JS)
        if path == "/" or path == "/index.html":
            file_path = os.path.join(WEB_DIR, "index.html")
        else:
            rel_path = path.lstrip("/")
            try:
                file_path = str(safe_join(WEB_DIR, rel_path))
            except UnsafePathError:
                self.send_error(404, f"Ruta no encontrada: {path}")
                return

        if os.path.isfile(file_path):
            mime, _ = mimetypes.guess_type(file_path)
            if not mime:
                mime = "text/plain"
            if file_path.endswith(".js"):
                mime = "application/javascript"
            elif file_path.endswith(".css"):
                mime = "text/css"

            with open(file_path, "rb") as f:
                content = f.read()

            self.send_response(200)
            self.send_header("Content-Type", f"{mime}; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(content)
            return

        self.send_error(404, f"Ruta no encontrada: {path}")

    def serve_file_with_range(self, full_path, mime_type):
        file_size = os.path.getsize(full_path)
        range_header = self.headers.get("Range")

        if range_header:
            try:
                ranges = range_header.replace("bytes=", "").split("-")
                start = int(ranges[0]) if ranges[0] else 0
                end = int(ranges[1]) if ranges[1] else file_size - 1
            except Exception:
                start = 0
                end = file_size - 1

            start = max(0, min(start, file_size - 1))
            end = max(start, min(end, file_size - 1))
            length = end - start + 1

            self.send_response(206)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
            self.send_header("Content-Length", str(length))
            self.send_header("Accept-Ranges", "bytes")
            self.send_cors_headers()
            self.end_headers()

            try:
                with open(full_path, "rb") as f:
                    f.seek(start)
                    bytes_to_send = length
                    while bytes_to_send > 0:
                        chunk = f.read(min(bytes_to_send, 64 * 1024))
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        bytes_to_send -= len(chunk)
            except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError, OSError):
                pass
        else:
            self.send_response(200)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(file_size))
            self.send_header("Accept-Ranges", "bytes")
            self.send_cors_headers()
            self.end_headers()
            try:
                with open(full_path, "rb") as f:
                    while True:
                        chunk = f.read(64 * 1024)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
            except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError, OSError):
                pass

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        if not self.require_trusted_origin():
            return
        if not self.require_token():
            return

        editor = get_editor_api()
        if editor.handle(self, "POST", path, parse_qs(parsed.query), body):
            return
        if get_workspace_api().handle(self, "POST", path, parse_qs(parsed.query), body):
            return

        # 0. Controles de ejecución: cancelar render y apagar el servidor.
        if path in ("/api/stop_main", "/api/shutdown"):
            resultado = detener_render_actual() if path == "/api/stop_main" else apagar_servidor()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(resultado).encode("utf-8"))
            return

        # 1. Guardar cambios en el archivo activo (main.py o pasos_algebraicos.txt)
        if path == "/api/save_main":
            try:
                data = json.loads(body.decode("utf-8"))
                new_code = data.get("code", "")
                target_file = data.get("file", "main.py")
                slug = _project_slug(parse_qs(parsed.query), data)
                if target_file == "pasos_algebraicos.txt":
                    with open(_pasos_path(slug), "w", encoding="utf-8") as f:
                        f.write(new_code)
                    msg = "pasos_algebraicos.txt guardado con éxito"
                else:
                    with open(_main_path(slug), "w", encoding="utf-8") as f:
                        f.write(new_code)
                    msg = "main.py guardado con éxito"
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"status": "saved", "message": msg, "file": target_file}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # 1b. Subir archivo de audio local al servidor
        if path == "/api/upload_audio":
            try:
                if len(body) > MAX_UPLOAD_BYTES:
                    self.send_response(413)
                    self.send_cors_headers()
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "El audio supera el límite de 50 MB."}).encode("utf-8"))
                    return
                raw_filename = self.headers.get("X-Filename", "audio.mp3")
                clean_name = os.path.basename(raw_filename).replace(" ", "_")
                extension = os.path.splitext(clean_name)[1].lower()
                if extension not in ALLOWED_AUDIO_EXTENSIONS:
                    self.send_response(415)
                    self.send_cors_headers()
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": f"Extensión no permitida: {extension or '(sin extensión)'}"}).encode("utf-8"))
                    return
                if not clean_name:
                    clean_name = f"audio_{int(time.time())}.mp3"
                dest_path = str(safe_join(AUDIO_DIR, clean_name))
                with open(dest_path, "wb") as f:
                    f.write(body)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "uploaded",
                    "url": f"/audios/{clean_name}",
                    "name": clean_name,
                    "size": len(body)
                }).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # 1c. Integrar y multiplexar audio con video para descarga sincronizada
        if path == "/api/merge_audio_video":
            try:
                data = json.loads(body.decode("utf-8")) if body else {}
                audio_name = data.get("audio_name", "")
                start_offset = float(data.get("start_offset", 0.0))
                video_url = data.get("video_url", "")

                # 1. Localizar archivo de video
                video_path = None
                if video_url:
                    clean_rel = video_url.split("?")[0].lstrip("/")
                    if clean_rel.startswith("media/"):
                        try:
                            candidate = safe_join(MEDIA_DIR, clean_rel[len("media/"):])
                        except UnsafePathError:
                            candidate = None
                        if candidate and candidate.is_file():
                            video_path = str(candidate)
                if not video_path:
                    video_path = find_latest_video_file()

                if not video_path or not os.path.isfile(video_path):
                    self.send_response(400)
                    self.send_cors_headers()
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "No se encontró el video generado para integrar audio."}).encode("utf-8"))
                    return

                # 2. Localizar archivo de audio
                clean_audio_name = os.path.basename(audio_name)
                if not clean_audio_name:
                    self.send_response(400)
                    self.send_cors_headers()
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Debes indicar el nombre del audio."}).encode("utf-8"))
                    return
                try:
                    audio_path = str(safe_join(AUDIO_DIR, clean_audio_name))
                except UnsafePathError:
                    audio_path = ""
                if not audio_path or not os.path.isfile(audio_path):
                    self.send_response(400)
                    self.send_cors_headers()
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": f"Audio '{clean_audio_name}' no encontrado en el servidor."}).encode("utf-8"))
                    return

                # 3. Obtener duración exacta del video con ffprobe
                duration = get_media_duration(video_path)
                if not duration or duration <= 0:
                    duration = 60.0

                exports_dir = os.path.join(MEDIA_DIR, "exports")
                os.makedirs(exports_dir, exist_ok=True)
                base_name = os.path.splitext(os.path.basename(video_path))[0]
                output_name = f"{base_name}_con_audio_{int(time.time())}.mp4"
                output_path = os.path.join(exports_dir, output_name)

                # 4. FFmpeg: Extraer sección del audio, sincronizar y empaquetar con el video
                cmd = [
                    "ffmpeg", "-y",
                    "-ss", str(max(0.0, start_offset)),
                    "-t", str(duration),
                    "-i", audio_path,
                    "-i", video_path,
                    "-filter_complex", "[0:a]apad[aout]",
                    "-map", "1:v:0",
                    "-map", "[aout]",
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-t", str(duration),
                    output_path
                ]

                proc = subprocess.run(cmd, capture_output=True, text=True)
                if proc.returncode != 0:
                    raise Exception(f"FFmpeg multiplex error: {proc.stderr[:300]}")

                rel_export = os.path.relpath(output_path, MEDIA_DIR).replace("\\", "/")
                download_url = f"/media/{rel_export}?t={int(os.path.getmtime(output_path))}"

                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "success",
                    "download_url": download_url,
                    "filename": output_name,
                    "duration": duration,
                    "start_offset": start_offset
                }).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # 2. Ejecutar y transmitir en vivo. La fuente de verdad es la ruta que
        # llega en `path`: nunca se cae silenciosamente a main.py.
        if path == "/api/run_main":
            try:
                data = json.loads(body.decode("utf-8")) if body else {}
                target = resolve_run_target(data, parse_qs(parsed.query))
            except workspace.WorkspaceError as exc:
                self.send_response(exc.status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"error": exc.message}).encode("utf-8"))
                return
            except Exception as exc:
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"No se pudo preparar la ejecución: {exc}"}).encode("utf-8"))
                return

            threading.Thread(
                target=run_main_task,
                args=(target["quality"], target["script"], target["format"]),
                daemon=True,
            ).start()

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "started",
                "message": f"Ejecutando {target['file']}...",
                "file": target["file"],
                "path": target["path"],
                "project": target["slug"],
                "script": target["script"],
                "sha256": target.get("sha256"),
                "size": target.get("size"),
            }).encode("utf-8"))
            return

        # 1d. Cálculo analítico de tiempos para Short
        if path == "/api/short/calculate":
            try:
                data = json.loads(body.decode("utf-8")) if body else {}
                metodo = data.get("metodo", "biseccion")
                max_iter = int(data.get("max_iteraciones", 4))
                tiempo_deseado = float(data.get("tiempo_deseado", 60.0))
                
                from manim_studio.motor.plantillas.short import calcular_vector_tiempos, verificar_duracion_short
                
                vector = calcular_vector_tiempos(metodo=metodo, max_iteraciones=max_iter, tiempo_deseado=tiempo_deseado)
                verif = verificar_duracion_short(metodo=metodo, max_iteraciones=max_iter, tiempos=vector.to_dict(), limite_segundos=60.0)
                
                res = {
                    "status": "success",
                    "metodo": metodo,
                    "max_iteraciones": max_iter,
                    "tiempo_objetivo": tiempo_deseado,
                    "tiempo_estimado": vector.tiempo_estimado,
                    "factor_escalado": vector.factor_escalado,
                    "claves": vector.claves,
                    "vector": list(vector),
                    "mapa": vector.to_dict(),
                    "desglose": verif
                }
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps(res).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # 1e. Generación completa de código Manim para Short
        if path == "/api/short/generate":
            try:
                data = json.loads(body.decode("utf-8")) if body else {}
                metodo = data.get("metodo", "biseccion")
                funcion = data.get("funcion", "exp(x) - 3*(x**2)")
                tiempo_deseado = float(data.get("tiempo_deseado", 60.0))
                max_iter = int(data.get("max_iteraciones", 4))
                a = float(data.get("a", 0.0))
                b = float(data.get("b", 1.5))
                x0 = float(data.get("x0", 1.5))
                x_min = float(data.get("x_min", -0.5))
                x_max = float(data.get("x_max", 2.0))
                tolerancia = float(data.get("tolerancia", 0.0001))
                save_to_main = bool(data.get("save_to_main", False))

                from manim_studio.motor.plantillas.short import generar_codigo_short
                res = generar_codigo_short(
                    metodo=metodo,
                    funcion=funcion,
                    tiempo_deseado=tiempo_deseado,
                    max_iteraciones=max_iter,
                    a=a, b=b, x0=x0,
                    x_min=x_min, x_max=x_max,
                    tolerancia=tolerancia,
                    save_to_main=save_to_main,
                    ruta_main=_main_path(_project_slug(parse_qs(parsed.query), data))
                )

                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps(res).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # 1f. Generar ejercicio aleatorio (POST)
        if path == "/api/short/random_exercise":
            metodo_param = ""
            try:
                data = json.loads(body.decode("utf-8")) if body else {}
                metodo_param = data.get("metodo", "").strip()
            except Exception:
                pass
            self.handle_random_exercise(metodo_param)
            return

        self.send_error(404, "Endpoint POST no encontrado")

    def do_PUT(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        if not self.require_trusted_origin():
            return
        if not self.require_token():
            return

        editor = get_editor_api()
        if editor.handle(self, "PUT", parsed.path, parse_qs(parsed.query), body):
            return
        if get_workspace_api().handle(self, "PUT", parsed.path, parse_qs(parsed.query), body):
            return

        self.send_error(404, "Endpoint PUT no encontrado")

current_main_process = None
process_lock = threading.Lock()
httpd_instance = None
render_cancel_requested = False


def detener_render_actual() -> dict:
    """Punto de entrada HTTP para cancelar el render en curso."""

    global render_cancel_requested
    resultado = detener_render(
        get_process=lambda: current_main_process,
        process_lock=process_lock,
        emitir=broadcast_sse,
        terminar=terminate_process_tree,
    )
    if resultado["status"] == "stopped":
        render_cancel_requested = True
    return resultado


def apagar_servidor() -> dict:
    """Punto de entrada HTTP para apagar el servidor de forma controlada."""

    return solicitar_apagado(
        get_servidor=lambda: httpd_instance,
        emitir=broadcast_sse,
    )


def run_main_task(quality="low_quality", script_path=None, format_id="16:9"):
    """Ejecuta main.py con salida sin búfer y transmite logs en tiempo real vía SSE."""
    global current_main_process, render_cancel_requested
    render_cancel_requested = False
    with process_lock:
        previous = current_main_process
        if previous and previous.poll() is None:
            terminate_process_tree(previous)

    script_path = script_path or _main_path()
    script_name = os.path.basename(script_path)
    broadcast_sse("status", {"state": "rendering", "message": f"Iniciando ejecución de {script_name}..."})
    broadcast_sse("log", {"level": "info", "text": "=========================================================="})
    broadcast_sse("log", {"level": "info", "text": f"> Ejecutando: python -u {script_name}"})

    python_exe = sys.executable
    venv_py = os.path.join(BASE_DIR, ".venv", "Scripts", "python.exe")
    if os.path.isfile(venv_py):
        python_exe = venv_py

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    env["MANIM_STUDIO_HEADLESS"] = "1"  # Evita abrir reproductores nativos bloqueantes
    env["MANIM_QUALITY"] = quality
    env["MANIM_FORMAT"] = str(format_id)
    # La clase `AnimadorGrafico` lee esta variable: sin ella el MP4 cae en
    # src/manim_studio/motor/media y `find_latest_video()` nunca lo encuentra.
    env["MANIM_MEDIA_DIR"] = MEDIA_DIR

    start_time = time.time()
    proc = None
    popen_kwargs = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    try:
        proc = subprocess.Popen(
            [python_exe, "-u", script_path],
            cwd=BASE_DIR,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            encoding="utf-8",
            errors="replace",
            **popen_kwargs,
        )
        with process_lock:
            current_main_process = proc

        for line in proc.stdout:
            line_str = line.rstrip("\r\n")
            if not line_str:
                continue
            level = "info"
            if "ERROR" in line_str or "Traceback" in line_str or "Exception" in line_str:
                level = "error"
            elif "WARNING" in line_str or "major issue" in line_str:
                level = "warning"
            elif "Animation" in line_str:
                level = "progress"
            broadcast_sse("log", {"level": level, "text": line_str})

        proc.wait()
        duration = round(time.time() - start_time, 2)

        if render_cancel_requested:
            broadcast_sse("status", {
                "state": "cancelled",
                "message": "Ejecución detenida por el usuario.",
            })
        elif proc.returncode == 0:
            # Sólo se considera éxito si el video se generó en esta ejecución;
            # así un render anterior no simula que se ejecutó el archivo viejo.
            latest_vid = find_latest_video(since=start_time - 1)
            if latest_vid:
                broadcast_sse("log", {"level": "success", "text": f"✓ Ejecución exitosa de {script_name} ({duration}s)"})
                broadcast_sse("status", {
                    "state": "success",
                    "message": f"Renderizado exitoso ({duration}s)",
                    "video_url": latest_vid
                })
                broadcast_sse("video", {"video_url": latest_vid})
            elif find_latest_video():
                broadcast_sse("log", {"level": "warning", "text": "Proceso finalizado, pero el video más reciente es anterior a esta ejecución."})
                broadcast_sse("log", {"level": "success", "text": f"✓ Proceso de {script_name} finalizado ({duration}s)"})
                broadcast_sse("status", {
                    "state": "success",
                    "message": "Proceso finalizado sin video nuevo",
                })
            else:
                broadcast_sse("log", {"level": "warning", "text": "Proceso finalizado, pero no se localizó archivo de video MP4."})
                broadcast_sse("status", {"state": "error", "message": "No se encontró el archivo de video."})
        else:
            broadcast_sse("log", {"level": "error", "text": f"✗ Error en la ejecución de {script_name} (código {proc.returncode}) tras {duration}s."})
            broadcast_sse("status", {"state": "error", "message": f"Falló con código {proc.returncode}"})

    except Exception as ex:
        broadcast_sse("log", {"level": "error", "text": f"[Excepción al ejecutar {script_name}]: {ex}"})
        broadcast_sse("status", {"state": "error", "message": str(ex)})
    finally:
        with process_lock:
            if current_main_process is proc:
                current_main_process = None

def run_server(port: int = 5000) -> None:
    """Arranca el servidor local y mantiene la referencia global para apagarlo."""

    global httpd_instance
    ThreadingHTTPServer.allow_reuse_address = True

    ensure_directories()
    projects.ensure_initial_project()
    workspace.apply_saved_context()

    while True:
        try:
            httpd = ThreadingHTTPServer(("127.0.0.1", port), ManimStudioHandler)
            break
        except OSError as err:
            if err.errno == 10048 or "Address already in use" in str(err):
                print(f"Puerto {port} ocupado, intentando con {port + 1}...")
                port += 1
                continue
            raise

    httpd.daemon_threads = True
    httpd_instance = httpd
    puerto_real = httpd.server_address[1]
    print("\n" + "=" * 56)
    print(f"  [MANIM STUDIO] Servidor activo en: http://localhost:{puerto_real}")
    print("  Ctrl+C o el boton 'Apagar servidor' para terminar.")
    print("=" * 56 + "\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[MANIM STUDIO] Servidor detenido por el usuario.")
    finally:
        httpd.server_close()
        httpd_instance = None
        print("[MANIM STUDIO] Proceso terminado.")


if __name__ == "__main__":
    puerto = int(os.environ.get("MANIM_STUDIO_PORT", "5000"))
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        puerto = int(sys.argv[1])
    run_server(puerto)
