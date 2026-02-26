#!/usr/bin/env bash
# Instalador todo-en-uno para Ryzen Master Commander.
# Uso: desde el repositorio clonado, ejecutar: ./Build/install.sh
# Opción: ./Build/install.sh --system  (instala en /opt, requiere sudo para los archivos)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
INSTALL_SYSTEM=false
if [ "${1:-}" = "--system" ]; then
  INSTALL_SYSTEM=true
fi

# Comprobar que estamos en el repositorio completo (no solo la carpeta Build)
if [ ! -f "$REPO_ROOT/requirements.txt" ] || [ ! -d "$REPO_ROOT/src" ]; then
  echo "Error: hace falta el repositorio completo."
  echo "  Debe existir $REPO_ROOT/requirements.txt y $REPO_ROOT/src/"
  echo "  Copia o clona la carpeta completa del proyecto (no solo Build/) y ejecuta: ./Build/install.sh"
  exit 1
fi

if [ "$INSTALL_SYSTEM" = true ]; then
  INSTALL_DIR="/opt/ryzen-master-commander"
  echo "Modo sistema: se instalará en $INSTALL_DIR (se usará sudo para copiar archivos)."
else
  INSTALL_DIR="${HOME}/.local/ryzen-master-commander"
  echo "Modo usuario: se instalará en $INSTALL_DIR"
fi

echo "Origen (repositorio): $REPO_ROOT"
echo "Destino:              $INSTALL_DIR"
echo ""

# Dependencias de sistema (Python, venv, pip, libs Qt para la GUI)
echo "[1/6] Comprobando dependencias de sistema..."
if ! command -v python3 &>/dev/null; then
  echo "Se necesita python3. Instálalo con: sudo apt update && sudo apt install -y python3 python3-venv python3-pip"
  exit 1
fi
# Instalar paquetes necesarios (en Ubuntu recién instalado suelen faltar)
NEEDED=""
for pkg in python3-venv python3-pip libxcb-cursor0; do
  if ! dpkg -l "$pkg" &>/dev/null 2>&1; then
    NEEDED="$NEEDED $pkg"
  fi
done
if [ -n "$NEEDED" ]; then
  echo "Instalando:$NEEDED"
  sudo apt-get update -qq
  sudo apt-get install -y $NEEDED
fi

# Crear directorio de instalación y copiar fuentes necesarios
echo "[2/6] Copiando fuentes a $INSTALL_DIR..."
if [ "$INSTALL_SYSTEM" = true ]; then
  sudo mkdir -p "$INSTALL_DIR"
  sudo cp -r "$REPO_ROOT/src" "$REPO_ROOT/bin" "$REPO_ROOT/polkit" "$REPO_ROOT/share" "$REPO_ROOT/tdp_profiles" "$REPO_ROOT/img" "$INSTALL_DIR/"
  sudo cp "$REPO_ROOT/requirements.txt" "$REPO_ROOT/version.txt" "$INSTALL_DIR/"
  sudo chown -R "$USER:$USER" "$INSTALL_DIR"
else
  mkdir -p "$INSTALL_DIR"
  cp -r "$REPO_ROOT/src" "$REPO_ROOT/bin" "$REPO_ROOT/polkit" "$REPO_ROOT/share" "$REPO_ROOT/tdp_profiles" "$REPO_ROOT/img" "$INSTALL_DIR/"
  cp "$REPO_ROOT/requirements.txt" "$REPO_ROOT/version.txt" "$INSTALL_DIR/"
fi

# Script de ejecución en el directorio instalado
echo "[3/6] Configurando script de ejecución..."
cat > "$INSTALL_DIR/run-ryzen-master-commander.sh" << 'RUNSCRIPT'
#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
fi
export PYTHONPATH="$(pwd):${PYTHONPATH}"
exec "$(pwd)/.venv/bin/python" -m src.main
RUNSCRIPT
chmod +x "$INSTALL_DIR/run-ryzen-master-commander.sh"

# Entorno virtual e dependencias Python
echo "[4/6] Creando entorno virtual e instalando dependencias Python..."
cd "$INSTALL_DIR"
python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt

# Polkit (ryzenadj/nbfc sin pedir contraseña cada vez)
echo "[5/6] Instalando política polkit..."
POLKIT_SRC="$INSTALL_DIR/polkit/com.merrythieves.ryzenadj.policy"
POLKIT_DST="/usr/share/polkit-1/actions/com.merrythieves.ryzenadj.policy"
if [ -f "$POLKIT_SRC" ]; then
  sudo cp "$POLKIT_SRC" "$POLKIT_DST"
  sudo chown root:root "$POLKIT_DST"
  sudo chmod 0644 "$POLKIT_DST"
  echo "   Política instalada. Opcional: sudo systemctl daemon-reload && sudo systemctl restart polkit"
else
  echo "   No se encontró $POLKIT_SRC; omitiendo polkit."
fi

# Acceso directo en el escritorio
echo "[6/6] Creando acceso directo en el escritorio..."
DESKTOP_DIR=""
[ -d "$HOME/Escritorio" ] && DESKTOP_DIR="$HOME/Escritorio"
[ -d "$HOME/Desktop" ]   && DESKTOP_DIR="${DESKTOP_DIR:-$HOME/Desktop}"
ICON="$INSTALL_DIR/img/icon.png"
[ ! -f "$ICON" ] && ICON=""
if [ -n "$DESKTOP_DIR" ]; then
  SHORTCUT="$DESKTOP_DIR/RyzenMasterCommander.desktop"
  cat > "$SHORTCUT" << DESKTOP
[Desktop Entry]
Type=Application
Name=Ryzen Master Commander
Comment=Monitorizar y controlar TDP y ventilador Ryzen
Exec=$INSTALL_DIR/run-ryzen-master-commander.sh
Icon=$ICON
Terminal=false
Categories=Utility;System;
DESKTOP
  chmod +x "$SHORTCUT"
  echo "   Creado: $SHORTCUT"
else
  echo "   No se encontró Escritorio ni Desktop; no se creó acceso directo."
fi

echo ""
echo "=== Instalación completada ==="
echo "  Ejecutar la aplicación:"
echo "    $INSTALL_DIR/run-ryzen-master-commander.sh"
echo ""
echo "  Dependencias opcionales (control TDP y ventilador):"
echo "    - ryzenadj: sudo snap install ryzenadj --beta --devmode"
echo "    - nbfc:     según tu distro (p. ej. AUR, o desde nbfc-linux)"
echo ""
