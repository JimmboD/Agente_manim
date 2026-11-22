#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ -x ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
elif [ -x ".venv/Scripts/python.exe" ]; then
  PYTHON=".venv/Scripts/python.exe"
else
  echo "[MANIM STUDIO] No se encontró el entorno virtual .venv" >&2
  echo "Crealo con: python -m venv .venv" >&2
  exit 1
fi

exec "$PYTHON" scripts/iniciar.py "$@"
