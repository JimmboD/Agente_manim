# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el proyecto sigue [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Modo **Estudio** por defecto: editor de código, chat, terminal, vista previa
  con audio, árbol de archivos y carril de plantillas en una sola ventana.
- Espacio de trabajo con raíces `escenas`, `plantillas`, `mis-plantillas`,
  `audios` y `media`; API `/api/workspace/*` para explorar, abrir, crear, mover,
  borrar y subir audios.
- Plantillas existentes sugeridas en el carril, creación desde el código actual
  y favoritos guardados localmente.
- Asistente de código con `CODE_SYSTEM_PROMPT`, propuestas que devuelven código
  completo y diff unificado, validación con `ast.parse` y aplicación solo tras
  confirmación.
- Ajustes con color libre y presets, calidad `480p`/`720p`/`1080p` y formato
  `16:9`/`9:16`/`1:1`.
- Indicador de guardado sobre la terminal y control global `Ctrl+S` con
  `sha256` para evitar sobrescrituras concurrentes.
- Botón **IR** para abrir el editor de escenas como vista auxiliar.
- Pruebas unitarias para workspace y asistente de código.

### Changed

- La navegación lateral se reduce a Estudio, Ajustes y Documentación; Scratch y
  Shorts salen de la nav pero su código se conserva.
- El archivo `.py` abierto manda: `Ejecutar` guarda y lanza ese archivo usando la
  calidad y el formato activos; el IR pasa a ser una vista auxiliar.
- Documentación de usuario y técnica actualizada al nuevo flujo del Estudio.

### Fixed

- Se evita el guardado duplicado al pulsar `Ctrl+S` desde CodeMirror.
- El botón `Ejecutar` usa el archivo abierto y el mensaje de error nombra el
  script real, no siempre `main.py`.
- La vista auxiliar IR vuelve a mostrarse cuando se activa desde el Estudio.
- Las rutas de plantillas de usuario se codifican correctamente para nombres con
  acentos o espacios.

### Security

- Las nuevas rutas `/api/workspace/*` exigen token local y `Origin` de confianza,
  además de rutas confinadas a las raíces permitidas.

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
