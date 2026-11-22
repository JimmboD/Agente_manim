# Manim Studio

Editor local de animaciones matemáticas construido sobre [Manim CE](https://www.manim.community/).
La interfaz tiene un modo **Estudio** por defecto: el archivo `.py` abierto es
la fuente de verdad, el asistente propone cambios y el usuario revisa el diff
antes de aplicarlos. La previsualización se actualiza mientras se trabaja.
El anterior editor de IR permanece como vista auxiliar (botón **IR** sobre el
editor).

> En el modo Estudio el asistente puede proponer código Python completo, pero
> no lo guarda: el servidor valida la sintaxis y calcula el diff; solo «Aplicar»
> o `Ctrl+S` escriben en disco. En la vista auxiliar de IR el modelo solo
> produce parches validados y el código se regenera de forma determinista.

## Características

- **Modo Estudio**: editor de código, chat, terminal, vista previa con audio,
  árbol de archivos y carril de plantillas en una sola ventana.
- **Flujo híbrido**: edición manual del `.py` o propuesta del asistente, siempre
  con revisión → aplicación. Nada se guarda sin confirmación.
- **Control de cambios**: si el archivo cambia en disco mientras lo editas, la
  escritura se rechaza con `409` en lugar de sobrescribir tu trabajo.
- **Archivos y plantillas**: abrir, crear, mover, borrar y subir audios desde el
  árbol; cargar plantillas existentes, crear una desde el código actual y
  marcar favoritas.
- **Ajustes completos**: color libre con presets, calidad `480p`/`720p`/`1080p`
  y formato `16:9`/`9:16`/`1:1`.
- **Render aislado**: cada previsualización corre en un subproceso con su propio
  `MANIM_MEDIA_DIR`, con logs en vivo por SSE y cancelación explícita.
- **Tres formatos**: `16:9`, `9:16` y `1:1`, con layouts y encuadre adaptados.
- **Audio**: sube una grabación, ajusta el offset manualmente y exporta el video
  con la voz integrada.
- **Persistencia local**: SQLite (`var/data/editor.db`) para proyectos, escenas,
 revisiones, mensajes del chat e historial de renders.
- **Seguridad local**: token de sesión, validación de `Origin`, `safe_join` para
  rutas y allowlist en el AST del código generado.
- **LLM real u local**: proveedor OpenAI-compatible por `.env`, con
  `MockProvider` automático si no hay clave configurada.
- **Acceso local ahora, remoto después**: el servidor escucha en `127.0.0.1`; la
  exposición remota requerirá autenticación y HTTPS.

## Requisitos

- Python 3.11 o superior.
- Dependencias del motor: Manim CE 0.21, NumPy, SciPy, SymPy y Pillow.
- En Windows, el lanzador usa `.venv\Scripts\python.exe` si existe.

## Instalación

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
```

El paquete se instala en modo editable como `manim-studio`. El lanzador también
lo instala automáticamente si aún no es importable.

Para usar un modelo real:

```powershell
Copy-Item .env.example .env
# Edita .env y rellena LLM_API_KEY
```

Sin `LLM_API_KEY` el editor funciona con el proveedor local (`mock`), útil para
desarrollo y pruebas. Opciones soportadas: OpenAI, DeepSeek, OpenRouter y Ollama
(consulta los ejemplos en `.env.example`).

## Uso

```powershell
.\scripts\iniciar.bat
```

En Linux/macOS:

```bash
./scripts/iniciar.sh
```

O directamente:

```powershell
.\.venv\Scripts\python.exe scripts\iniciar.py --port 5000
```

El lanzador elige un puerto libre, abre el navegador y muestra la URL activa.
También puedes ejecutar `manim-studio` si el entorno está activado.

Controles de la sesión:

- **Ejecutar archivo** (sobre el editor) guarda y lanza el `.py` abierto con
  Manim, usando la calidad y el formato de *Ajustes*.
- **Detener** (junto a *Ejecutar*) cancela el render en curso sin apagar el servidor.
- **Apagar servidor** (panel lateral → *Sesión del servidor*) pide confirmación
  y termina el proceso local de forma controlada.
- `Ctrl+S` guarda el archivo activo aunque el foco esté en otro panel; la franja
  sobre la terminal indica si hay cambios guardados o sin guardar.

## Estructura

```
src/manim_studio/
  editor/     IR, validación, codegen, DB, jobs, LLM, API, workspace y asistente de código
  motor/      planos, álgebra, plantillas y generador de ejercicios
  web/        interfaz HTML/CSS/JS (Pizarra Analítica, modo Estudio y studio.js)
  __init__.py expone ROOT y PAQUETE_DIR
  control.py  lógica de detener render y apagar servidor
  lanzador.py arranque, puerto libre y apertura del navegador
  servidor.py HTTP local, SSE y endpoints heredados
scripts/      iniciar.py / iniciar.bat / iniciar.sh
escenas/      main.py y pasos_algebraicos.txt (archivos de trabajo)
var/          data/, media/ y audios/ generados en local (ignorados por Git)
docs/         editor, estilo, prompt del sistema y referencia técnica
```

## Flujo del editor

### Modo Estudio (`.py` manda)

1. `GET /api/workspace/files/tree` y `/files/read` alimentan el árbol y el
   editor. `Ctrl+S` usa `POST /files/write` con el `sha256` leído; un cambio
   concurrente devuelve `409`.
2. `POST /api/workspace/code/propose` envía mensaje, ruta, código y algo de
   historia. Devuelve `{reply, summary, code, code_diff, path}` sin escribir.
   El frontend muestra el diff y ofrece **Aplicar**/**Descartar**.
3. `POST /api/workspace/code/apply` revalida el `sha256` y escribe solo tras
   la confirmación del usuario.
4. `POST /api/run_main` ejecuta el archivo abierto (o el canónico `escenas/main.py`)
   con `MANIM_QUALITY` y `MANIM_FORMAT`; los logs llegan por SSE.
5. Las plantillas se listan en `/api/workspace/templates`; «Agregar» crea una
   desde el código actual y la estrella la marca como favorita (preferencia
   local del navegador).

### Vista auxiliar de IR

1. `POST /api/editor/scenes/{id}/chat` devuelve
   `{reply, summary, patch, code_diff, base_revision, proposal_id}` y **no**
   modifica la escena.
2. El frontend muestra el diff y ofrece **Aplicar**, **Descartar** y **Deshacer**.
3. `POST /api/editor/scenes/{id}/apply` exige `base_revision`, valida el parche
   y solo entonces incrementa la revisión, regenera el código y encola el render.
4. `GET /api/editor/jobs/{id}` informa del estado; cada cambio cancela el render
   anterior de la misma escena.

La API completa está resumida en [`docs/EDITOR.md`](docs/EDITOR.md) y la
referencia del motor en
[`docs/REFERENCIA_TECNICA.md`](docs/REFERENCIA_TECNICA.md).

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -t .
.\.venv\Scripts\python.exe -m compileall -q src tests scripts escenas
```

La suite cubre validación del IR, generación de código, control de revisiones,
proveedores LLM y seguridad de rutas/token.

## Documentación

- [Editor de escenas](docs/EDITOR.md)
- [Sistema visual «Pizarra Analítica»](docs/ESTILO.md)
- [Prompt del sistema para Manim](docs/PROMPT_SISTEMA_MANIM.md)
- [Referencia técnica del motor Manim](docs/REFERENCIA_TECNICA.md)
- [Registro de cambios](CHANGELOG.md)
