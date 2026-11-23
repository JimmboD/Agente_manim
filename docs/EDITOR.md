# Estudio de escenas

Manim Studio trabaja en un único modo principal, **Estudio**. Cada proyecto es
una carpeta física en `var/proyectos/<slug>/` con su propia carpeta `escenas/`.
El archivo `.py` abierto es la fuente de verdad: se edita directamente,
`Ctrl+S` lo guarda y el asistente solo propone cambios que el usuario revisa
como diff antes de aplicar. La previsualización se actualiza mientras se
trabaja.

No hay botón **IR** ni vista de editor de IR: los módulos de IR siguen en el
backend, pero no forman parte de la interfaz.

## Cómo arrancar

```powershell
.\scripts\iniciar.bat
```

El lanzador comprueba el entorno, elige un puerto libre y abre el navegador.
También funciona con `.\.venv\Scripts\python.exe scripts\iniciar.py` o, desde un
entorno con el paquete instalado, `manim-studio`.

Abre `http://127.0.0.1:5000/`. La vista **Estudio** está activa por defecto; el
panel lateral solo muestra **Estudio** y **Ajustes y documentación**, además del
botón **Apagar servidor**.

- Proyectos: `var/proyectos/<slug>/escenas/`.
- Proyecto activo: `var/data/active_project`.
- Plantillas de usuario: `var/plantillas/`; plantillas del sistema:
  `src/manim_studio/motor/plantillas/`.
- Ajustes: `var/data/settings.json`.
- Base de datos: `var/data/editor.db` (SQLite, WAL).
- Token de sesión: `var/data/session_token` (se crea al primer arranque).
- Medios de cada job: `var/media/editor/<job_id>/`.
- Audios subidos: `var/audios/` (no se versionan MP3).
- Todo lo anterior bajo `var/` está ignorado por Git.

Los botones **Detener** (junto a *Ejecutar*) y **Apagar servidor** (panel lateral
→ *Sesión del servidor*) permiten cortar el render en curso y terminar el proceso
local sin usar `Ctrl+C`.

Para usar un modelo real, copia `.env.example` a `.env` y rellena la clave. Sin
`LLM_API_KEY` el editor sigue funcionando con el proveedor local (`mock`).

## Modo Estudio

### Interfaz

- **Sidebar izquierda**: carrusel de proyectos (crear desde un título,
  seleccionar y borrar), pestañas **Archivos** y **Plantillas**, y botones como
  iconos estilo VS Code: nuevo archivo, nueva carpeta, mover/renombrar, borrar,
  subir audio y actualizar.
- **Árbol «Proyecto»**: archivos del proyecto activo. El usuario los añade y
  quita desde la sidebar; son documentos del proyecto, no plantillas.
- **Panel de herramientas**: una sola ventana con pestañas **Editor**,
  **Agente** y **Audio**.
- **Consola**: franja fija abajo con los logs SSE; la franja superior indica si
  hay cambios guardados o sin guardar y permite forzar el guardado.
- **Vista previa**: columna de la derecha; reproduce el MP4 generado y ofrece
  descarga, reinicio y exportación con audio.
- **Editor + Ejecutar/Detener**: *Ejecutar* guarda antes de lanzar el `.py`
  abierto con la calidad y el formato activos.
- **Chat de código**: el asistente devuelve una propuesta con diff; **Aplicar**
  la escribe en disco y **Descartar** la descarta. Nada se guarda sin revisión.
- **Ajustes**: color libre con presets, calidad (`480p`, `720p`, `1080p`),
  formato (`16:9`, `9:16`, `1:1`), la casilla «Desbloquear edición de las
  plantillas originales» y la documentación técnica integrada.

### Flujo

1. `GET /api/workspace/files/tree` y `GET /api/workspace/files/read?path=...`
   alimentan el árbol y el editor. La raíz pública `escenas` se muestra como
   «Proyecto» y apunta a `var/proyectos/<slug>/escenas/` del proyecto activo.
   La lectura devuelve `code` y `sha256`.
2. `Ctrl+S` usa `POST /api/workspace/files/write` con el `sha256` leído. Si el
   archivo cambió en disco mientras se editaba, la respuesta es `409` en lugar
   de sobrescribirlo.
3. `POST /api/workspace/code/propose` recibe `message`, `path`, `code` e
   `history`. Devuelve `{reply, summary, code, code_diff, path}` sin escribir.
   El servidor valida la sintaxis con `ast.parse` y calcula el diff unificado.
4. `POST /api/workspace/code/apply` vuelve a validar `sha256` antes de escribir.
   Solo se ejecuta cuando el usuario pulsa **Aplicar**.
5. `POST /api/run_main` toma como fuente de verdad la ruta `path` del archivo
   abierto. Debe ser un `.py` existente dentro de la carpeta **Proyecto** del
   proyecto activo; si no, responde `400` sin caer a `main.py`. La terminal
   muestra la ruta resuelta. Las llamadas heredadas que no envían `path` (Short)
   conservan su comportamiento con `code`/`file`.
6. `GET /api/workspace/templates` lista las plantillas. `POST
   /api/workspace/templates` crea una con el código abierto en
   `var/plantillas/`; la estrella es una preferencia local del navegador. Las
   plantillas del sistema son de solo lectura salvo que se active el ajuste.

### API del espacio de trabajo

| Método | Ruta | Uso |
| --- | --- | --- |
| `GET` | `/api/workspace/projects` | Proyectos, proyecto activo y ajustes |
| `POST` | `/api/workspace/projects` | Crea un proyecto desde `title` |
| `POST` | `/api/workspace/projects/select` | Selecciona un `slug` |
| `POST` | `/api/workspace/projects/delete` | Borra un `slug` |
| `GET` | `/api/workspace/settings` | Ajustes persistidos |
| `POST` | `/api/workspace/settings` | Actualiza `unlockSystemTemplates` |
| `GET` | `/api/workspace/files/tree` | Raíces y nodos del árbol de archivos |
| `GET` | `/api/workspace/files/read?path=...` | Código y `sha256` de un archivo |
| `POST` | `/api/workspace/files/write` | Escribe con control de `sha256` |
| `POST` | `/api/workspace/files/create` | Crea archivo o carpeta |
| `POST` | `/api/workspace/files/move` | Mueve o renombra |
| `POST` | `/api/workspace/files/delete` | Elimina archivos o carpetas editables |
| `POST` | `/api/workspace/files/upload` | Sube un audio a `var/audios/` |
| `GET` | `/api/workspace/templates` | Plantillas del sistema y del usuario |
| `POST` | `/api/workspace/templates` | Crea una plantilla con el código abierto |
| `POST` | `/api/workspace/code/propose` | Propone código + diff, sin guardar |
| `POST` | `/api/workspace/code/apply` | Aplica una propuesta ya revisada |
| `POST` | `/api/run_main` | Ejecuta la ruta `path` validada del proyecto activo |

En la API, `mis-plantillas` es la raíz pública de `var/plantillas/` y
`escenas` la del proyecto activo.

Todas las rutas mutantes exigen `X-Session-Token` y un `Origin` local.

## Backend de IR (sin interfaz)

Los módulos `src/manim_studio/editor/ir.py`, `codegen.py` y `api.py` siguen en el
repositorio, pero no hay vista de editor de IR, botón **IR** ni panel IR. El IR
no forma parte del flujo del Estudio ni se expone en la navegación.

## Seguridad local

- Toda petición mutante exige `X-Session-Token` (comparación en tiempo
  constante). El token se entrega en `/api/editor/bootstrap`, que no es legible
  desde otros orígenes.
- `Origin` se valida contra `127.0.0.1`, `localhost` y `[::1]` en el puerto
  activo; no se emite CORS comodín.
- Las rutas del espacio de trabajo se resuelven dentro de raíces permitidas
  (`escenas` → proyecto activo, `plantillas`, `mis-plantillas`, `audios`,
  `media`) y pasan por `safe_join`, que rechaza `..` con `/` y con `\`.
- `/api/run_main` solo acepta archivos `.py` existentes dentro de la carpeta
  **Proyecto**; cualquier otra ruta se rechaza con `400`.
- Subidas de audio limitadas por extensión y tamaño; los MP3 no se versionan.
- El historial de la conversación del Estudio se envía al servidor en `history`;
  la clave del proveedor LLM no se expone nunca al frontend.
- **Acceso local ahora, remoto después**: el servidor escucha en `127.0.0.1` y
  no está preparado para exponerse a Internet sin autenticación y HTTPS.

## Formatos, calidad y color

`16:9`, `9:16` y `1:1` comparten el mismo motor. El formato se traduce en
`MANIM_FORMAT`; `src/manim_studio/motor/planos/generar_plano.py` ajusta
`frame_width`, `pixel_width` y el encuadre de la cámara. La calidad se traduce
en `MANIM_QUALITY` (`low_quality`/480p, `medium_quality`/720p,
`high_quality`/1080p). El color libre de *Ajustes* se aplica como variable CSS
y se guarda en `localStorage`, junto con el tema y el formato.

## Interfaz

El sistema visual «Pizarra Analítica» se reparte en:

- `src/manim_studio/web/tokens.css`: tipografías, espaciado y colores.
- `src/manim_studio/web/components.css`: botones, campos y paneles.
- `src/manim_studio/web/index.css`: layout del Estudio (sidebar, panel de
  pestañas, consola fija y vista previa) y responsive.
- `src/manim_studio/web/icons.js`: iconos SVG de línea, sin librerías externas.
- `src/manim_studio/web/app.js`: estado global, navegación, ajustes, ejecución y
  documentación integrada.
- `src/manim_studio/web/studio.js`: proyectos, árbol, plantillas, guardado y
  chat de código.
- CodeMirror 5 (CDN): editor real del `.py`, con resaltado y números de línea.
  Si los CDN no están disponibles, se usa un `textarea` como fallback.

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -t .
.\.venv\Scripts\python.exe -m compileall -q src scripts tests escenas
node --check src\manim_studio\web\app.js
node --check src\manim_studio\web\studio.js
```

La suite (69 pruebas) cubre seguridad de rutas y tokens, validación del IR,
generación de código, SQLite, proveedores LLM, reparación de parches, conflictos
de revisión, workspace, proyectos físicos, migración, ajustes, resolución
estricta de la ejecución y propuestas de código.

## Proveedor LLM

`src/manim_studio/editor/llm.py` define la interfaz `LLMProvider` y dos
implementaciones:

- `MockProvider`: heurísticas en español, sin red (formato, iteraciones, ritmo,
  velocidad y código completo para el asistente del Estudio).
- `OpenAICompatibleProvider`: habla `/chat/completions` con OpenAI, DeepSeek,
  OpenRouter u Ollama. `get_provider()` elige el proveedor según `.env`.

El Estudio usa `CODE_SYSTEM_PROMPT` en
`src/manim_studio/editor/prompts.py`: pide un JSON con `reply`, `summary` y
`code` completo; el servidor valida la sintaxis, genera el diff y respeta el
`sha256` del archivo para detectar cambios concurrentes (`409`).

Variables de `.env`:

```dotenv
LLM_PROVIDER=openai
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
LLM_API_KEY=sk-...
LLM_TIMEOUT=45
LLM_MAX_TOKENS=1200
```

Si `LLM_PROVIDER` es `ollama`, no hace falta clave. Si no hay clave para los
demás proveedores, `get_provider()` cae a `MockProvider` y `/api/editor/bootstrap`
lo indica en `llm.mock`.
