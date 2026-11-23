# Manim Studio

Editor local de animaciones matemáticas construido sobre [Manim CE](https://www.manim.community/).
La interfaz se abre en el **Estudio**: cada proyecto vive en una carpeta
`var/proyectos/<slug>/`, el archivo `.py` abierto es la fuente de verdad y el
usuario revisa el diff antes de aplicar cambios. La previsualización se
actualiza mientras se trabaja.

> El asistente puede proponer el archivo `.py` o `.txt` completo, pero no lo
> guarda: el servidor valida el contenido y calcula el diff; solo «Aplicar» o
> `Ctrl+S` escriben en disco. No hay representación intermedia: el buffer del
> editor es la fuente de verdad.

## Características

- **Modo Estudio**: editor a ancho completo, agente en la sidebar izquierda y
  franja inferior **Terminal | Audio** debajo del video.
- **Proyectos físicos**: `var/proyectos/<slug>/escenas/` para cada proyecto; se
  crean desde un título, se seleccionan y se borran desde la barra lateral.
- **Flujo híbrido**: edición manual del `.py`/`.txt` o propuesta del asistente,
  siempre con revisión → aplicación. Nada se guarda sin confirmación.
- **Revisión visual**: antes de aplicar, el diff aparece con filas verdes/rojas
  estilo GitHub y el editor resalta las líneas afectadas sin modificar el buffer.
- **Contexto por modos**: `buffer`, `files`, `folder` y `project`. Los archivos
  adicionales se resuelven en servidor y son solo lectura.
- **Control de cambios**: si el archivo cambia en disco mientras lo editas, la
  escritura se rechaza con `409` en lugar de sobrescribir tu trabajo.
- **Sidebar unificada**: lista desplegable de proyectos, pestañas **Archivos**,
  **Plantillas** y **Agente**, y acciones como iconos estilo VS Code (nuevo
  archivo, nueva carpeta, mover/renombrar, borrar, subir audio y actualizar).
- **Plantillas separadas**: las del usuario son globales (`var/plantillas/`) y
  se crean desde la pestaña **Plantillas**; las del sistema son de solo lectura
  salvo que se active el ajuste correspondiente.
- **Ajustes completos**: color libre con presets, calidad `480p`/`720p`/`1080p`,
  formato `16:9`/`9:16`/`1:1` y opción «Desbloquear edición de las plantillas
  originales».
- **Render aislado**: cada previsualización corre en un subproceso, escribe el
  MP4 en `var/media/videos/` y se muestra al terminar; los logs llegan por SSE y
  la ejecución se puede cancelar.
- **Tres formatos**: `16:9`, `9:16` y `1:1`, con layouts y encuadre adaptados.
- **Audio**: sube una grabación, ajusta el offset manualmente y exporta el video
  con la voz integrada.
- **Persistencia local**: proyectos, plantillas de usuario, audios y medios bajo
  `var/` (ignorado por Git). El estado del proyecto vive en archivos de texto;
  no se usa base de datos.
- **Seguridad local**: token de sesión, validación de `Origin`, `safe_join` para
  rutas, validación `sha256` y `ast.parse` para el `.py` activo.
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

- **Ejecutar archivo** (sobre el editor) escribe el código actual del buffer en
  el `.py` abierto y lo lanza con Manim, usando la calidad y el formato de
  *Ajustes*.
- **Detener** (junto a *Ejecutar*) cancela el render en curso sin apagar el servidor.
- **Apagar servidor** (panel lateral → *Sesión del servidor*) pide confirmación
  y termina el proceso local de forma controlada.
- `Ctrl+S` guarda el archivo activo aunque el foco esté en otro panel; la pestaña
  **Terminal** indica si hay cambios guardados o sin guardar.

## Estructura

```
src/manim_studio/
  editor/     proyectos, workspace, bundles, contexto, LLM, API y asistente
              de código; sin representación intermedia
  motor/      planos, álgebra, plantillas del sistema y generador de ejercicios
  web/        interfaz HTML/CSS/JS (Pizarra Analítica, app.js y studio.js)
  __init__.py expone ROOT y PAQUETE_DIR
  control.py  lógica de detener render y apagar servidor
  lanzador.py arranque, puerto libre y apertura del navegador
  servidor.py HTTP local, SSE y endpoints
scripts/      iniciar.py / iniciar.bat / iniciar.sh
escenas/      contenido heredado que se copia al proyecto inicial
var/          proyectos/<slug>/escenas/, plantillas/, data/, media/ y audios/
              generados en local (ignorados por Git)
docs/         editor, estilo, prompt del sistema y referencia técnica
```

## Flujo del editor

### Modo Estudio (`.py` manda)

1. `GET /api/workspace/files/tree` y `GET /api/workspace/files/read` alimentan
   el árbol y el editor. `Ctrl+S` usa `POST /api/workspace/files/write` con el
   `sha256` leído; un cambio concurrente devuelve `409`.
2. `POST /api/workspace/code/propose` envía mensaje, ruta, código, historia y
   `context` (`buffer`/`files`/`folder`/`project`). Devuelve `reply`, `summary`,
   `code`, `code_diff`, `hunks`, `stats` y `path`, sin escribir.
   El frontend pinta el diff tipo GitHub, marca el editor y ofrece
   **Aplicar**/**Descartar**.
3. `POST /api/workspace/code/apply` revalida el `sha256` y escribe solo tras
   la confirmación del usuario.
4. `POST /api/run_main` ejecuta la ruta `path` del archivo abierto: debe ser un
   `.py` existente dentro de la carpeta **Proyecto** del proyecto activo. Una
   ruta inválida responde `400`, sin caer a `main.py`; la terminal muestra la
   ruta resuelta. Las llamadas heredadas que solo envían `code`/`file` siguen
   funcionando para Short. Los logs llegan por SSE.
5. Las plantillas se listan en `/api/workspace/templates`. Las del sistema
   (`src/manim_studio/motor/plantillas/`) son de solo lectura; las del usuario
   viven en `var/plantillas/`, se crean desde la pestaña **Plantillas** y la
   estrella las marca como favoritas (preferencia local del navegador).
6. «Pasos algebraicos» es un bundle: `POST /api/workspace/templates/deploy`
   crea `escenas/pasos_algebraicos.py` y `escenas/pasos_algebraicos.txt` en el
   proyecto activo, abre el `.py` y pide confirmación (con `sha256`) antes de
   sobrescribir archivos existentes.

### Sin representación intermedia

El IR y sus módulos de soporte (`ir.py`, `codegen.py`, `api.py`, `db.py`,
`jobs.py` y `scenes/`) se eliminaron. El asistente trabaja solo con el archivo
activo y con contexto de solo lectura resuelto por el servidor.

La API del estudio está resumida en [`docs/EDITOR.md`](docs/EDITOR.md). La
referencia del motor se consulta dentro de **Ajustes y documentación** y también
está disponible en
[`docs/REFERENCIA_TECNICA.md`](docs/REFERENCIA_TECNICA.md).

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -t .
.\.venv\Scripts\python.exe -m compileall -q src tests scripts escenas
```

La suite (48 pruebas) cubre proyectos físicos, migración del contenido
heredado, ajustes, resolución estricta de la ejecución, bundles multiarchivo,
contexto, propuestas `.py`/`.txt`, proveedores LLM, control de revisiones y
seguridad de rutas/token.

## Documentación

- [Estudio: editor, proyectos y plantillas](docs/EDITOR.md)
- [Sistema visual «Pizarra Analítica»](docs/ESTILO.md)
- [Prompt del sistema para Manim](docs/PROMPT_SISTEMA_MANIM.md)
- [Referencia técnica del motor Manim](docs/REFERENCIA_TECNICA.md)
- [Registro de cambios](CHANGELOG.md)
