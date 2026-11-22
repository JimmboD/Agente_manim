@echo off
setlocal
cd /d "%~dp0.."

if not exist ".venv\Scripts\python.exe" (
  echo [MANIM STUDIO] No se encontro el entorno virtual .venv
  echo Crealo con: python -m venv .venv
  pause
  exit /b 1
)

".venv\Scripts\python.exe" "scripts\iniciar.py" %*
if errorlevel 1 (
  echo.
  echo [MANIM STUDIO] El servidor termino con errores.
  pause
)
endlocal
