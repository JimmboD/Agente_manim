# Editor de escenas

Manim Studio trabaja en un único modo principal, **Estudio**. El archivo `.py`
abierto es la fuente de verdad: se edita directamente, `Ctrl+S` lo guarda y el
asistente solo propone cambios que el usuario revisa como diff antes de aplicar.
La previsualización se actualiza mientras se trabaja.

El antiguo editor de IR permanece como **vista auxiliar**: se abre con el botón
**IR** situado sobre el editor. Las vistas de Scratch y Shorts ya no aparecen en
la navegación, pero su código se ha conservado en el proyecto.

## Cómo arrancar

```powershell
.\scripts\iniciar.bat
```

El lanzador comprueba el entorno, elige un puerto libre y abre el navegador.
También funciona con `.\.venv\Scripts\python.exe scripts\iniciar.py` o, desde un
entorno con el paquete instalado, `manim-studio`.

Abre `http://127.0.0.1:5000/`. La vista **Estudio** está activa por defecto; el
panel lateral solo muestra **Estudio**, **Ajustes** y **Documentación**, además
del botón **Apagar servidor**.

- Base de datos: `var/data/editor.db` (SQLite, WAL).
- Token de sesión: `var/data/session_token` (se crea al primer arranque).
- Medios de cada job: `var/media/editor/<job_id>/`.
- Audios subidos: `var/audios/` (ignorado por Git; no se versionan MP3).
- Todos esos directorios están ignorados por Git.

Los botones **Detener** (junto a *Ejecutar*) y **Apagar servidor** (panel lateral
→ *Sesión del servidor*) permiten cortar el render en curso y terminar el proceso
local sin usar `Ctrl+C`.

Para usar un modelo real, copia `.env.example` a `.env` y rellena la clave. Sin
`LLM_API_KEY` el editor sigue funcionando con el proveedor local (`mock`).

## Modo Estudio

### Interfaz

- **Carril de plantillas**: busca, carga, crea una desde el código actual y
  marca favoritas. Las plantillas existentes se sugieren por nombre.
- **Árbol de archivos**: explora `escenas/`, `mis-plantillas/` y `audios/`; abre,
  crea, mueve, borra y sube audios. `plantillas/` y `media/` son de solo lectura.
- **Editor + Ejecutar/Detener**: el botón guarda antes de lanzar el `.py` abierto.
- **Salida visual**: reproduce el MP4 generado y ofrece descarga, reinicio y
  exportación con audio.
- **Consola**: logs SSE del motor. La franja superior indica si hay cambios
  guardados o sin guardar y permite forzar el guardado.
- **Chat de código**: el asistente devuelve una propuesta con diff; **Aplicar**
  la escribe en disco y **Descartar** la descarta. Nada se guarda sin revisión.
- **Ajustes**: color libre con presets, calidad (`480p`, `720p`, `1080p`) y
  formato (`16:9`, `9:16`, `1:1`).

### Flujo

1. `GET /api/workspace/files/tree` y `GET /api/workspace/files/read?path=...`
   alimentan el árbol y el editor. La lectura devuelve `code` y `sha256`.
2. `Ctrl+S` usa `POST /api/workspace/files/write` con el `sha256` leído. Si el
   archivo cambió en disco mientras se editaba, la respuesta es `409` en lugar
   de sobrescribirlo.
3. `POST /api/workspace/code/propose` recibe `message`, `path`, `code` e
   `history`. Devuelve `{reply, summary, code, code_diff, path}` sin escribir.
   El servidor valida la sintaxis con `ast.parse` y calcula el diff unificado.
4. `POST /api/workspace/code/apply` vuelve a validar `sha256` antes de escribir.
   Solo se ejecuta cuando el usuario pulsa **Aplicar**.
5. `POST /api/run_main` ejecuta el archivo abierto (o el canónico
   `escenas/main.py`) con `MANIM_QUALITY` y `MANIM_FORMAT`; los logs llegan por
   SSE y el render se puede cancelar.
6. `GET /api/workspace/templates` lista las plantillas. `POST
   /api/workspace/templates` crea una desde el código actual; la estrella es una
   preferencia local del navegador.

### API del espacio de trabajo

| Método | Ruta | Uso |
| --- | --- | --- |
| `GET` | `/api/workspace/files/tree` | Raíces y nodos del árbol de archivos |
| `GET` | `/api/workspace/files/read?path=...` | Código y `sha256` de un archivo |
| `POST` | `/api/workspace/files/write` | Escribe con control de `sha256` |
| `POST` | `/api/workspace/files/create` | Crea archivo o carpeta |
| `POST` | `/api/workspace/files/move` | Mueve o renombra |
| `POST` | `/api/workspace/files/delete` | Elimina (solo raíces editables) |
| `POST` | `/api/workspace/files/upload` | Sube un audio a `audios/` |
| `GET` | `/api/workspace/templates` | Plantillas del sistema y del usuario |
| `POST` | `/api/workspace/templates` | Crea una plantilla desde código |
| `POST` | `/api/workspace/code/propose` | Propone código + diff, sin guardar |
| `POST` | `/api/workspace/code/apply` | Aplica una propuesta ya revisada |

Todas estas rutas mutantes exigen `X-Session-Token` y un `Origin` local.

## Vista auxiliar de IR

1. El IR (`src/manim_studio/editor/ir.py`) valida función, dominio, intervalo,
   tolerancia, iteraciones, ritmo (beats), layout y narración. La expresión
   Python se analiza con `ast` y solo admite una lista blanca de nombres y
   funciones matemáticas.
2. `src/manim_studio/editor/codegen.py` genera un script delgado que incrusta el
   IR y llama a `src/manim_studio/editor/scenes/biseccion.py`. En esta vista el
   modelo solo propone parches sobre el IR; el código se regenera de forma
   determinista en el servidor.
3. `POST /api/editor/scenes/{id}/chat` devuelve `{reply, summary, patch,
   code_diff, base_revision, proposal_id}` y **no guarda ni renderiza**. El
   frontend muestra el diff y ofrece **Aplicar**, **Descartar** y **Deshacer**.
4. `POST /api/editor/scenes/{id}/apply` exige `base_revision`. Si la escena
   cambió mientras se revisaba la propuesta, responde `409`; un parche inválido
   responde `422`. Solo entonces se incrementa `revision`, se regenera el código
   y se encola el render.
5. `src/manim_studio/editor/jobs.py` crea un subproceso con su propio
   `MANIM_MEDIA_DIR`, guarda logs y estado en la tabla `renders` y permite
   cancelación.

### API del editor de IR

| Método | Ruta | Uso |
| --- | --- | --- |
| `GET` | `/api/editor/bootstrap` | Proyectos, formatos, calidades, token e IR por defecto |
| `GET` | `/api/editor/projects` | Lista de proyectos |
| `GET` | `/api/editor/projects/{id}` | Proyecto y sus escenas |
| `POST` | `/api/editor/projects` | Crea proyecto + escena inicial |
| `POST` | `/api/editor/projects/{id}/scenes` | Añade una escena |
| `GET` | `/api/editor/scenes/{id}` | Escena con IR, código, revisión y último render |
| `PUT` | `/api/editor/scenes/{id}` | Guarda IR/título y regenera código |
| `GET` | `/api/editor/scenes/{id}/renders` | Historial de renders |
| `GET` | `/api/editor/scenes/{id}/chat` | Historial de conversación |
| `POST` | `/api/editor/scenes/{id}/chat` | Pide una propuesta (no modifica la escena) |
| `POST` | `/api/editor/scenes/{id}/apply` | Aplica parche o IR con control de revisión |
| `POST` | `/api/editor/scenes/{id}/render` | Encola un job (`format`, `quality`) |
| `GET` | `/api/editor/jobs/{id}` | Estado, logs y URL del video |
| `POST` | `/api/editor/jobs/{id}/cancel` | Cancela el render |

## Seguridad local

- Toda petición mutante exige `X-Session-Token` (comparación en tiempo
  constante). El token se entrega en `/bootstrap`, que no es legible desde
  otros orígenes.
- `Origin` se valida contra `127.0.0.1`, `localhost` y `[::1]` en el puerto
  activo; no se emite CORS comodín.
- Las rutas del espacio de trabajo se resuelven dentro de raíces permitidas
  (`escenas`, `plantillas`, `mis-plantillas`, `audios`, `media`) y pasan por
  `safe_join`, que rechaza `..` con `/` y con `\`.
- Subidas de audio limitadas por extensión y tamaño; los MP3 no se versionan.
- Los mensajes del chat se guardan en SQLite; la clave del proveedor LLM no se
  expone nunca al frontend.
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
- `src/manim_studio/web/components.css`: botones, campos, paneles y vista IR.
- `src/manim_studio/web/index.css`: layout del modo Estudio y responsive.
- `src/manim_studio/web/icons.js`: iconos SVG de línea, sin librerías externas.
- `src/manim_studio/web/app.js`: estado global, navegación, ajustes y ejecución.
- `src/manim_studio/web/studio.js`: árbol, plantillas, guardado y chat de código.
- CodeMirror 5 (CDN): editor real del `.py`, con resaltado y números de línea.
  Si los CDN no están disponibles, se usa un `textarea` como fallback.

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -t .
.\.venv\Scripts\python.exe -m compileall -q src scripts tests escenas
node --check src\manim_studio\web\app.js
node --check src\manim_studio\web\studio.js
node --check src\manim_studio\web\editor.js
```

La suite cubre seguridad de rutas y tokens, validación del IR, generación de
código, SQLite, proveedores LLM, reparación de parches, conflictos de revisión,
workspace (árbol/escritura/plantillas) y propuestas de código.

## Proveedor LLM

`src/manim_studio/editor/llm.py` define la interfaz `LLMProvider` y dos
implementaciones:

- `MockProvider`: heurísticas en español, sin red (formato, iteraciones, ritmo,
  velocidad y código completo para el asistente del Estudio).
- `OpenAICompatibleProvider`: habla `/chat/completions` con OpenAI, DeepSeek,
  OpenRouter u Ollama. `get_provider()` elige el proveedor según `.env`.

Hay dos prompts complementarios:

- `CODE_SYSTEM_PROMPT` en `src/manim_studio/editor/prompts.py`: propuestas de
  código para el Estudio. Devuelve JSON con `reply`, `summary` y `code`; el
  servidor valida sintaxis y genera el diff.
- El prompt de IR de la vista auxiliar exige un JSON con `reply`, `summary` y
  `patch`, y solo permite tocar `title`, `format`, `function`, `params`,
  `beats`, `layout` y `narration`.

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
demás proveedores, `get_provider()` cae a `MockProvider` y `/bootstrap` lo
indica en `llm.mock`.
