"""Controles de ejecución del estudio local.

Toda la lógica de "detener" y "apagar" vive aquí, con dependencias inyectadas,
para poder probarla sin levantar un servidor ni lanzar subprocesos reales.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Callable

Emitir = Callable[[str, dict], None]


def detener_render(
    *,
    get_process: Callable[[], Any],
    process_lock: threading.Lock,
    emitir: Emitir,
    terminar: Callable[[Any], None],
) -> dict:
    """Termina el render activo, si lo hay, sin apagar el servidor."""

    with process_lock:
        process = get_process()

    if process is None or process.poll() is not None:
        emitir("status", {"state": "cancelled", "message": "No había ninguna ejecución activa."})
        return {"status": "idle"}

    terminar(process)
    emitir("log", {"level": "warning", "text": "Ejecución detenida por el usuario."})
    emitir("status", {
        "state": "cancelled",
        "message": "Ejecución detenida por el usuario.",
    })
    return {"status": "stopped"}


def solicitar_apagado(
    *,
    get_servidor: Callable[[], Any],
    emitir: Emitir,
    retardo: float = 0.4,
) -> dict:
    """Avisa a la interfaz y detiene el servidor tras responder la petición."""

    emitir("status", {"state": "shutdown", "message": "Apagando Manim Studio..."})

    def _apagar() -> None:
        time.sleep(retardo)
        servidor = get_servidor()
        if servidor is not None:
            servidor.shutdown()

    threading.Thread(target=_apagar, daemon=True).start()
    return {"status": "shutting_down"}
