# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el proyecto sigue [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Modo **Estudio** por defecto: pestañas **Editor**, **Agente** y **Audio** en
  una sola ventana, consola fija abajo y vista previa a la derecha.
- Proyectos físicos en `var/proyectos/<slug>/`, cada uno con su carpeta
  `escenas/`. El proyecto inicial migra byte a byte el contenido heredado de
  `escenas/main.py` y `escenas/pasos_algebraicos.txt`; `var/` está ignorado por
  Git.
- Carrusel de proyectos en la sidebar izquierda: crear desde un título,
  seleccionar y borrar; los archivos del proyecto se añaden y quitan desde el
  árbol.
- Acciones del árbol como iconos estilo VS Code: nuevo archivo, nueva carpeta,
  mover/renombrar, borrar, subir audio y actualizar.
- Plantillas de usuario globales en `var/plantillas/`, creadas desde la pestaña
  **Plantillas**, con favoritos guardados localmente.
- Ajuste «Desbloquear edición de las plantillas originales», persistido en
  `var/data/settings.json`.
- Asistente de código con `CODE_SYSTEM_PROMPT`, propuestas que devuelven código
  completo y diff unificado, validación con `ast.parse` y aplicación solo tras
  confirmación.
- Ajustes con color libre y presets, calidad `480p`/`720p`/`1080p` y formato
  `16:9`/`9:16`/`1:1`.
- Indicador de guardado sobre la terminal y control global `Ctrl+S` con
  `sha256` para evitar sobrescrituras concurrentes.
- `tests/test_projects.py` para proyectos, migración, ajustes y resolución
  estricta de la ejecución; la suite queda en 69 pruebas.

### Changed

- La navegación lateral se reduce a **Estudio** y **Ajustes y documentación**;
  Scratch y Shorts salen de la nav pero su código se conserva.
- La carpeta del árbol que antes se llamaba «Escenas y código» ahora se llama
  «Proyecto» y apunta al proyecto activo; la ruta pública sigue siendo
  `escenas/...`.
- Las plantillas del sistema (`src/manim_studio/motor/plantillas/`) son de solo
  lectura por defecto y se separan de los documentos del proyecto.
- `POST /api/run_main` usa como fuente de verdad la ruta `path` del archivo
  abierto, validada como `.py` dentro de la carpeta Proyecto del proyecto
  activo. La terminal muestra la ruta resuelta y se conserva la compatibilidad
  con llamadas heredadas que solo envían `code`.
- Documentación de usuario y técnica actualizada al flujo del Estudio.

### Removed

- Interfaz y opción de IR: vista de editor de escenas, botón **IR** y panel IR
  del antiguo `editor.js`. Los módulos de IR siguen existiendo en backend, pero
  no tienen UI.
- Vista separada de documentación: `REFERENCIA_TECNICA.md` se visualiza dentro
  de Ajustes.

### Fixed

- Se evita el guardado duplicado al pulsar `Ctrl+S` desde CodeMirror.
- Ya no se cae silenciosamente a `main.py`: si la ruta de ejecución es inválida,
  `/api/run_main` responde `400` y el error nombra el motivo.
- Las rutas de plantillas de usuario se codifican correctamente para nombres con
  acentos o espacios.

### Security

- Las rutas `/api/workspace/*` exigen token local y `Origin` de confianza,
  además de rutas confinadas al proyecto activo y a las raíces permitidas.

## [0.1.0] - 2026-11-22

### Added

- Editor híbrido de escenas con representación intermedia (IR), validación por
  AST y generación determinista de código Manim.
- Asistente LLM con proveedores OpenAI-compatible y `MockProvider` local; las
  propuestas se revisan antes de aplicarse y muestran un diff del código.
- Control de revisiones con respuesta `409` ante cambios concurrentes y `422`
  para parches inválidos, con opción de deshacer.
- Jobs de render aislados, con logs en tiempo real por SSE, cancelación y
  estado persistido en SQLite.
- Previsualización automática en formatos `16:9`, `9:16` y `1:1`, con layouts
  adaptados y encuadre de cámara por formato.
- Subida de audio, ajuste manual de offset y exportación con voz integrada.
- Sistema visual «Pizarra Analítica», componentes reutilizables e iconos SVG
  propios; CodeMirror 5 con fallback a textarea.
- Lanzador multiplataforma (`scripts/iniciar.py`, `.bat`, `.sh`) con detección
  de entorno, puerto libre y apertura del navegador.
- Controles para detener el render en curso y apagar el servidor local, con
  confirmación en la interfaz y eventos SSE `cancelled`/`shutdown`.
- Documentación técnica reorganizada en `docs/` y registro de cambios.

### Changed

- Estructura migrada a un paquete instalable `src/manim_studio/` con dominios
  `editor`, `motor` y `web`; rutas centralizadas en `editor/config.py`.
- Artefactos generados (`data/`, `media/`, `audios/`) unificados bajo `var/` y
  exclusiones de Git actualizadas en consecuencia.
- Archivos de trabajo `main.py` y `pasos_algebraicos.txt` movidos a `escenas/`.
- Plantillas y módulos del motor renombrados a nombres ASCII importables; se
  eliminaron los hacks de `sys.path`/`sys.modules`.
- La vista de documentación consume `docs/REFERENCIA_TECNICA.md` en lugar del
  antiguo `READMI.md`.

### Security

- Token local `X-Session-Token` en todas las peticiones mutantes del editor.
- Validación estricta de `Origin`/CORS y `safe_join` para todas las rutas de
  archivos y plantillas.
- Allowlist de imports y llamadas en el código generado; el LLM nunca emite
  Python arbitrario.
