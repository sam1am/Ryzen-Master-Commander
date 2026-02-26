#!/usr/bin/env bash
set -e

echo "Instalando políticas de polkit para Ryzen Master Commander..."

if [ "$EUID" -ne 0 ]; then
  echo "Se requiere sudo para copiar la política a /usr/share/polkit-1/actions/"
  exec sudo "$0" "$@"
fi

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
POLKIT_SRC="$PROJECT_DIR/polkit/com.merrythieves.ryzenadj.policy"
POLKIT_DST="/usr/share/polkit-1/actions/com.merrythieves.ryzenadj.policy"

if [ ! -f "$POLKIT_SRC" ]; then
  echo "No se encuentra el archivo de política en: $POLKIT_SRC"
  exit 1
fi

cp "$POLKIT_SRC" "$POLKIT_DST"
chown root:root "$POLKIT_DST"
chmod 0644 "$POLKIT_DST"

echo "Política instalada en $POLKIT_DST"
echo "Es posible que tengas que reiniciar la sesión o ejecutar:"
echo "  sudo systemctl restart polkit"
echo "para que los cambios se apliquen."

