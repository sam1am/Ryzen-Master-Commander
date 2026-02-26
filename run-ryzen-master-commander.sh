#!/usr/bin/env bash
set -e

# Ir a la carpeta del proyecto
cd "$(dirname "$0")"

# Asegurar que el entorno virtual existe e instala dependencias básicas si hace falta
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
fi

# Añadir la carpeta del proyecto al PYTHONPATH para que se encuentre el paquete src
export PYTHONPATH="$(pwd):${PYTHONPATH}"

# Ejecutar como usuario (la sesión gráfica carga bien). La contraseña se pide
# una sola vez cuando la app use nbfc/ryzenadj (polkit/pkexec).
# Si ves error de "xcb" o "libxcb-cursor0", instala: sudo apt install libxcb-cursor0
exec "$(pwd)/.venv/bin/python" -m src.main

