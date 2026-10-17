import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import json
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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")
MEDIA_DIR = os.path.join(BASE_DIR, "media")
AUDIO_DIR = os.path.join(BASE_DIR, "audios")
os.makedirs(AUDIO_DIR, exist_ok=True)
MAIN_PY_PATH = os.path.join(BASE_DIR, "main.py")
PASOS_ALGEBRAICOS_PATH = os.path.join(BASE_DIR, "pasos_algebraicos.txt")
PLANTILLAS_DIR = os.path.join(BASE_DIR, "Plantillas")

TEMPLATE_MAP = {
    "regla_falsa": os.path.join("Plantillas", "Análisis numérico", "Regla falsa.py"),
    "biseccion": os.path.join("Plantillas", "Análisis numérico", "Bisección.py"),
    "newton_raphson": os.path.join("Plantillas", "Análisis numérico", "Newton-Raphson.py"),
    "derivada_limite": os.path.join("Plantillas", "Cálculo diferencial", "Derivada límite.py"),
    "serie_taylor": os.path.join("Plantillas", "Cálculo diferencial", "Serie de Taylor.py"),
    "integral": os.path.join("Plantillas", "Cálculo diferencial", "Integral.py"),
    "curva_polinomica": os.path.join("Plantillas", "Álgebra y geometría", "Curva polinómica.py"),
    "hud_algebra": os.path.join("Plantillas", "Álgebra y geometría", "HUD álgebra.py"),
    "pasos_algebraicos": os.path.join("Plantillas", "Álgebra y geometría", "Pasos algebráicos.txt"),
    "serie_fourier": os.path.join("Plantillas", "Ecuaciones diferenciales", "Serie de Fourier.py"),
    "purga_ciclo_vida": os.path.join("Plantillas", "Control y ciclo de vida", "Purga ciclo de vida.py"),
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

def find_latest_video():
    """Localiza el archivo de video .mp4 generado más reciente."""
    newest = find_latest_video_file()
    if newest:
        rel = "/" + os.path.relpath(newest, BASE_DIR).replace("\\", "/")
        return f"{rel}?t={int(os.path.getmtime(newest))}"
    return None

def find_latest_video_file():
    """Retorna la ruta absoluta del archivo de video .mp4 generado más reciente."""
    video_candidates = glob.glob(os.path.join(MEDIA_DIR, "videos", "**", "*.mp4"), recursive=True)
    video_files = [f for f in video_candidates if "partial_movie_files" not in f and "exports" not in f]
    if video_files:
        return max(video_files, key=os.path.getmtime)
    return None

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

def obtener_generador_ejercicios():
    global _generador_ejercicios_mod
    if _generador_ejercicios_mod is None:
        ruta = os.path.join(BASE_DIR, "Generador de ejercicios", "Analisis numerico.py")
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
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

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
            if target_file == "pasos_algebraicos.txt":
                file_path = PASOS_ALGEBRAICOS_PATH
            else:
                file_path = MAIN_PY_PATH

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

        # 2b. Obtener contenido de READMI.md para documentación
        if path == "/api/get_readme":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors_headers()
            self.end_headers()
            readme_path = os.path.join(BASE_DIR, "READMI.md")
            if not os.path.isfile(readme_path):
                readme_path = os.path.join(BASE_DIR, "README.md")
            readme_content = ""
            if os.path.isfile(readme_path):
                with open(readme_path, "r", encoding="utf-8") as f:
                    readme_content = f.read()
            self.wfile.write(json.dumps({"content": readme_content}).encode("utf-8"))
            return

        # 2c. Obtener plantilla matemática directamente desde la carpeta Plantillas
        if path == "/api/get_template":
            query = parse_qs(parsed.query)
            template_id = query.get("id", [""])[0].strip()
            req_file = query.get("file", [""])[0].strip()

            file_path = None
            if template_id in TEMPLATE_MAP:
                candidate = os.path.normpath(os.path.join(BASE_DIR, TEMPLATE_MAP[template_id]))
                if os.path.isfile(candidate):
                    file_path = candidate

            if not file_path and req_file:
                clean_rel = req_file.lstrip("/\\").replace("\\", "/")
                candidate = os.path.normpath(os.path.join(BASE_DIR, "Plantillas", clean_rel))
                if os.path.isfile(candidate):
                    file_path = candidate

            if not file_path and template_id:
                clean_id = template_id.lower().replace("-", "_").replace(" ", "_")
                for root, dirs, files in os.walk(os.path.join(BASE_DIR, "Plantillas")):
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
                self.wfile.write(json.dumps({"error": f"Plantilla '{template_id}' no encontrada en la carpeta Plantillas/"}).encode("utf-8"))
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
            full_path = os.path.normpath(os.path.join(MEDIA_DIR, rel_path))
            if os.path.isfile(full_path):
                self.serve_file_with_range(full_path, "video/mp4")
                return
            else:
                self.send_error(404, "Video no encontrado")
                return

        # 4b. Servir archivos de audio con soporte Range
        if path.startswith("/audios/"):
            rel_path = path[len("/audios/"):]
            full_path = os.path.normpath(os.path.join(AUDIO_DIR, rel_path))
            if os.path.isfile(full_path):
                mime, _ = mimetypes.guess_type(full_path)
                if not mime or not mime.startswith("audio/"):
                    mime = "audio/mpeg"
                self.serve_file_with_range(full_path, mime)
                return
            else:
                self.send_error(404, "Audio no encontrado")
                return

        # 5. Servir Frontend estático (HTML, CSS, JS)
        if path == "/" or path == "/index.html":
            file_path = os.path.join(WEB_DIR, "index.html")
        else:
            rel_path = path.lstrip("/")
            file_path = os.path.normpath(os.path.join(WEB_DIR, rel_path))

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

        # 1. Guardar cambios en el archivo activo (main.py o pasos_algebraicos.txt)
        if path == "/api/save_main":
            try:
                data = json.loads(body.decode("utf-8"))
                new_code = data.get("code", "")
                target_file = data.get("file", "main.py")
                if target_file == "pasos_algebraicos.txt":
                    with open(PASOS_ALGEBRAICOS_PATH, "w", encoding="utf-8") as f:
                        f.write(new_code)
                    msg = "pasos_algebraicos.txt guardado con éxito"
                else:
                    with open(MAIN_PY_PATH, "w", encoding="utf-8") as f:
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
                raw_filename = self.headers.get("X-Filename", "audio.mp3")
                clean_name = os.path.basename(raw_filename).replace(" ", "_")
                if not clean_name:
                    clean_name = f"audio_{int(time.time())}.mp3"
                dest_path = os.path.join(AUDIO_DIR, clean_name)
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
                    candidate = os.path.normpath(os.path.join(BASE_DIR, clean_rel))
                    if os.path.isfile(candidate):
                        video_path = candidate
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
                audio_path = os.path.join(AUDIO_DIR, clean_audio_name)
                if not os.path.isfile(audio_path):
                    audio_candidates = glob.glob(os.path.join(AUDIO_DIR, "*"))
                    if audio_candidates:
                        audio_path = audio_candidates[0]
                    else:
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
                output_name = "EscenaAutomatica_con_audio.mp4"
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

                rel_export = "/" + os.path.relpath(output_path, BASE_DIR).replace("\\", "/")
                download_url = f"{rel_export}?t={int(os.path.getmtime(output_path))}"

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

        # 2. Ejecutar y transmitir en vivo
        if path == "/api/run_main":
            quality = "low_quality"
            target_file = "main.py"
            try:
                data = json.loads(body.decode("utf-8")) if body else {}
                target_file = data.get("file", "main.py")
                if "code" in data and data["code"] is not None:
                    if target_file == "pasos_algebraicos.txt":
                        with open(PASOS_ALGEBRAICOS_PATH, "w", encoding="utf-8") as f:
                            f.write(data["code"])
                        # Garantizamos el runner python que consume pasos_algebraicos.txt
                        runner_code = (
                            'from Planos.generar_plano import AnimadorGrafico\n\n'
                            'if __name__ == "__main__":\n'
                            '    escena = AnimadorGrafico()\n'
                            '    escena.insertar_algebra("pasos_algebraicos.txt", tiempo_animacion=1.5, tiempo_espera=2.0)\n'
                            '    escena.desvanecer_todo(tiempo_animacion=1.5)\n'
                            '    escena.render(previsualizar=True)\n'
                        )
                        with open(MAIN_PY_PATH, "w", encoding="utf-8") as f:
                            f.write(runner_code)
                    else:
                        if data["code"].strip():
                            with open(MAIN_PY_PATH, "w", encoding="utf-8") as f:
                                f.write(data["code"])
                if "quality" in data and data["quality"]:
                    quality = data["quality"]
            except Exception:
                pass

            threading.Thread(target=run_main_task, args=(quality,), daemon=True).start()

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"status": "started", "message": f"Ejecutando {target_file}...", "file": target_file}).encode("utf-8"))
            return

        # 1d. Cálculo analítico de tiempos para Short
        if path == "/api/short/calculate":
            try:
                data = json.loads(body.decode("utf-8")) if body else {}
                metodo = data.get("metodo", "biseccion")
                max_iter = int(data.get("max_iteraciones", 4))
                tiempo_deseado = float(data.get("tiempo_deseado", 60.0))
                
                from Plantillas.Short import calcular_vector_tiempos, verificar_duracion_short
                
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

                from Plantillas.Short import generar_codigo_short
                res = generar_codigo_short(
                    metodo=metodo,
                    funcion=funcion,
                    tiempo_deseado=tiempo_deseado,
                    max_iteraciones=max_iter,
                    a=a, b=b, x0=x0,
                    x_min=x_min, x_max=x_max,
                    tolerancia=tolerancia,
                    save_to_main=save_to_main,
                    ruta_main=MAIN_PY_PATH
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

current_main_process = None
process_lock = threading.Lock()

def run_main_task(quality="low_quality"):
    """Ejecuta main.py con salida sin búfer y transmite logs en tiempo real vía SSE."""
    global current_main_process
    with process_lock:
        if current_main_process and current_main_process.poll() is None:
            try:
                current_main_process.terminate()
                time.sleep(0.3)
            except Exception:
                pass

    broadcast_sse("status", {"state": "rendering", "message": "Iniciando ejecución de main.py..."})
    broadcast_sse("log", {"level": "info", "text": "=========================================================="})
    broadcast_sse("log", {"level": "info", "text": f"> Ejecutando: python -u main.py"})

    python_exe = sys.executable
    venv_py = os.path.join(BASE_DIR, ".venv", "Scripts", "python.exe")
    if os.path.isfile(venv_py):
        python_exe = venv_py

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["MANIM_STUDIO_HEADLESS"] = "1"  # Evita abrir reproductores nativos bloqueantes
    env["MANIM_QUALITY"] = quality

    start_time = time.time()
    try:
        proc = subprocess.Popen(
            [python_exe, "-u", MAIN_PY_PATH],
            cwd=BASE_DIR,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            encoding="utf-8",
            errors="replace"
        )
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

        if proc.returncode == 0:
            latest_vid = find_latest_video()
            if latest_vid:
                broadcast_sse("log", {"level": "success", "text": f"✓ Ejecución exitosa de main.py ({duration}s)"})
                broadcast_sse("status", {
                    "state": "success",
                    "message": f"Renderizado exitoso ({duration}s)",
                    "video_url": latest_vid
                })
            else:
                broadcast_sse("log", {"level": "warning", "text": "Proceso finalizado, pero no se localizó archivo de video MP4."})
                broadcast_sse("status", {"state": "error", "message": "No se encontró el archivo de video."})
        else:
            broadcast_sse("log", {"level": "error", "text": f"✗ Error en la ejecución de main.py (código {proc.returncode}) tras {duration}s."})
            broadcast_sse("status", {"state": "error", "message": f"Falló con código {proc.returncode}"})

    except Exception as ex:
        broadcast_sse("log", {"level": "error", "text": f"[Excepción al ejecutar main.py]: {ex}"})
        broadcast_sse("status", {"state": "error", "message": str(ex)})
    finally:
        current_main_process = None

def run_server(port=5000):
    ThreadingHTTPServer.allow_reuse_address = True
    server_address = ("127.0.0.1", port)
    try:
        httpd = ThreadingHTTPServer(server_address, ManimStudioHandler)
        httpd.daemon_threads = True
        print(f"\n========================================================")
        print(f"  [MANIM STUDIO] Servidor activo en: http://localhost:{port}")
        print(f"========================================================\n")
        httpd.serve_forever()
    except OSError as err:
        if err.errno == 10048 or "Address already in use" in str(err):
            print(f"Puerto {port} ocupado, intentando con {port + 1}...")
            run_server(port + 1)
        else:
            raise err

if __name__ == "__main__":
    port = 5000
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    run_server(port)
