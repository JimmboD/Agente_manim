"""Punto de entrada del lanzador desde la raíz del proyecto.

Uso:
    .venv\\Scripts\\python.exe scripts\\iniciar.py [--port 5000] [--no-browser]
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from manim_studio.lanzador import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
