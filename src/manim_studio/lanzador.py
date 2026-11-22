"""Lanzador del servidor local de Manim Studio.

Se encarga de tres cosas: comprobar el entorno, elegir un puerto libre y
abrir el navegador. La lógica HTTP vive en :mod:`manim_studio.servidor`.
"""

from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import threading
import webbrowser

from manim_studio import ROOT


def python_del_proyecto() -> str:
    """Devuelve el intérprete del entorno virtual cuando existe."""

    venv = ROOT / ".venv"
    candidato = venv / "Scripts" / "python.exe" if os.name == "nt" else venv / "bin" / "python"
    return str(candidato) if candidato.is_file() else sys.executable


def asegurar_instalacion(python: str) -> None:
    """Instala el paquete en modo editable si aún no es importable."""

    comprobacion = subprocess.run(
        [python, "-c", "import manim_studio"],
        cwd=str(ROOT),
        capture_output=True,
    )
    if comprobacion.returncode == 0:
        return

    print("[MANIM STUDIO] Instalando el paquete en modo editable...")
    subprocess.run(
        [python, "-m", "pip", "install", "-e", ".", "--no-deps"],
        cwd=str(ROOT),
        check=True,
    )


def puerto_libre(inicio: int = 5000) -> int:
    """Busca el primer puerto TCP libre a partir de `inicio`."""

    for puerto in range(inicio, inicio + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sonda:
            if sonda.connect_ex(("127.0.0.1", puerto)) != 0:
                return puerto
    raise RuntimeError(f"No hay puertos libres entre {inicio} y {inicio + 99}.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lanza Manim Studio en el puerto local")
    parser.add_argument("--port", type=int, default=None, help="Puerto inicial (por defecto, 5000)")
    parser.add_argument("--no-browser", action="store_true", help="No abrir el navegador")
    args = parser.parse_args(argv)

    python = python_del_proyecto()
    os.environ["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + os.environ.get("PYTHONPATH", "")
    asegurar_instalacion(python)

    puerto = args.port or int(os.environ.get("MANIM_STUDIO_PORT", "5000"))
    puerto = puerto_libre(puerto)
    os.environ["MANIM_STUDIO_PORT"] = str(puerto)

    if not args.no_browser:
        threading.Timer(
            0.8,
            lambda: webbrowser.open(f"http://127.0.0.1:{puerto}/"),
        ).start()

    from manim_studio.servidor import run_server

    run_server(puerto)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
