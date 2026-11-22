# Editor de escenas

Editor híbrido de animaciones matemáticas: el usuario edita una representación
intermedia (IR) o pide cambios al asistente, y el servidor regenera el código,
guarda en SQLite y lanza un render aislado que se previsualiza en la misma
página.

## Cómo arrancar

```powershell
.\.venv\Scripts\python.exe server.py
```

Abre `http://127.0.0.1:5000/` y entra en **Editor de escenas**.

- Base de datos: `data/editor.db` (SQLite, WAL).
- Token de sesión: `data/session_token` (se crea al primer arranque).
- Medios de cada job: `media/editor/<job_id>/`.
- Ambos directorios están ignorados por Git.

## Flujo

1. **Escena → IR.** El IR (`app/ir.py`) valida función, dominio, intervalo,
   tolerancia, iteraciones, ritmo (beats), layout y narración. La expresión
   Python se analiza con `ast` y solo admite una lista blanca de nombres y
   funciones matemáticas.
2. **IR → código.** `app/codegen.py` genera un script delgado que incrusta el
   IR y llama a `app/scenes/biseccion.py`. El LLM nunca escribe el algoritmo:
   propone parches sobre el IR.
3. **Render.** `app/jobs.py` crea un subproceso con su propio `MANIM_MEDIA_DIR`,
   transmite logs por SSE y guarda el estado en la tabla `renders`.
4. **Previsualización.** El frontend consulta el job y reproduce el MP4 cuando
   termina. Cada cambio cancela el render anterior de esa escena.

## API (`/api/editor`)

| Método | Ruta | Uso |
| --- | --- | --- |
| `GET` | `/bootstrap` | Proyectos, formatos, calidades, token e IR por defecto |
| `GET` | `/projects` | Lista de proyectos |
| `GET` | `/projects/{id}` | Proyecto y sus escenas |
| `POST` | `/projects` | Crea proyecto + escena inicial |
| `POST` | `/projects/{id}/scenes` | Añade una escena |
| `GET` | `/scenes/{id}` | Escena con IR, código y último render |
| `PUT` | `/scenes/{id}` | Guarda IR/título y regenera código |
| `POST` | `/scenes/{id}/render` | Encola un job (`format`, `quality`) |
| `POST` | `/scenes/{id}/chat` | Pide un parche al LLM |
| `GET` | `/jobs/{id}` | Estado, logs y URL del video |
| `POST` | `/jobs/{id}/cancel` | Cancela el render |

## Seguridad local

- Toda petición mutante exige `X-Session-Token` (comparación en tiempo
  constante). El token se entrega en `/bootstrap`, que no es legible desde
  otros orígenes.
- `Origin` se valida contra `127.0.0.1`, `localhost` y `[::1]` en el puerto
  activo; no se emite CORS comodín.
- Todas las rutas de archivo pasan por `safe_join`, que resuelve enlaces y
  rechaza `..` tanto con `/` como con `\`.
- Subidas de audio limitadas a 50 MB y a extensiones de audio conocidas.

## Formatos

`16:9`, `9:16` y `1:1` comparten el mismo motor. El formato se traduce en
`MANIM_FORMAT`; `Planos/generar_plano.py` ajusta `frame_width`, `pixel_width`
y el encuadre de la cámara a la relación de aspecto activa.

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -t .
```

Cubren seguridad de rutas y tokens, validación del IR, generación de código,
SQLite y el proveedor LLM simulado.

## Proveedor LLM

`app/llm.py` define `LLMProvider` y un `MockProvider` con heurísticas en
español (velocidad, formato, iteraciones, tolerancia, intervalo, función,
colores y título). Para conectar un modelo real basta con implementar
`propose(message, ir, context)` y devolver un `LLMProposal` con un parche
validable por `merge_patch`.
