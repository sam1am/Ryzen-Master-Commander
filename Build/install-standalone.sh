#!/usr/bin/env bash
# Instalador independiente: debe estar FUERA del comprimido, en la misma carpeta que RyzenMasterCommander-bundle.tar.gz
# Uso: copia este script y RyzenMasterCommander-bundle.tar.gz a la misma carpeta; ejecuta: ./install-standalone.sh
# Opción: ./install-standalone.sh --system  (instala en /opt)

set -e

# El script debe estar en la misma carpeta que RyzenMasterCommander-bundle.tar.gz (p. ej. dentro de Build/)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUNDLE="$SCRIPT_DIR/RyzenMasterCommander-bundle.tar.gz"
INSTALL_SYSTEM=false
if [ "${1:-}" = "--system" ]; then
  INSTALL_SYSTEM=true
fi

if [ "$INSTALL_SYSTEM" = true ]; then
  INSTALL_DIR="/opt/ryzen-master-commander"
  echo "Modo sistema: se instalará en $INSTALL_DIR"
else
  INSTALL_DIR="${HOME}/.local/ryzen-master-commander"
  echo "Modo usuario: se instalará en $INSTALL_DIR"
fi

if [ ! -f "$BUNDLE" ]; then
  echo "Error: no se encuentra el comprimido."
  echo "  Coloca RyzenMasterCommander-bundle.tar.gz en la misma carpeta que este script:"
  echo "  $SCRIPT_DIR"
  exit 1
fi

echo "Comprimido: $BUNDLE"
echo "Destino:    $INSTALL_DIR"
echo ""

# [1/8] Instalar todas las dependencias de sistema (el usuario no tiene que instalar nada a mano)
echo "[1/8] Instalando dependencias de sistema (se pedirá contraseña sudo)..."
sudo apt-get update -qq
sudo apt-get install -y python3 python3-venv python3-pip libxcb-cursor0 lm-sensors
# En Ubuntu 24.04+ el venv necesita python3.X-venv (p. ej. python3.12-venv) para ensurepip
PYVER="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null)"
if [ -n "$PYVER" ]; then
  sudo apt-get install -y "python${PYVER}-venv"
fi

# [2/8] Descomprimir el .tar.gz en el directorio de instalación
echo "[2/8] Descomprimiendo RyzenMasterCommander-bundle.tar.gz en $INSTALL_DIR..."
if [ "$INSTALL_SYSTEM" = true ]; then
  sudo mkdir -p "$INSTALL_DIR"
  sudo tar xzf "$BUNDLE" -C "$INSTALL_DIR"
  sudo chown -R "$USER:$USER" "$INSTALL_DIR"
else
  mkdir -p "$INSTALL_DIR"
  tar xzf "$BUNDLE" -C "$INSTALL_DIR"
fi

# [3/8] Script de ejecución
echo "[3/8] Configurando script de ejecución..."
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

# [4/8] Entorno virtual y dependencias Python
echo "[4/8] Creando entorno virtual e instalando dependencias Python..."
cd "$INSTALL_DIR"
python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt

# [5/8] Polkit
echo "[5/8] Instalando política polkit..."
POLKIT_SRC="$INSTALL_DIR/polkit/com.merrythieves.ryzenadj.policy"
POLKIT_DST="/usr/share/polkit-1/actions/com.merrythieves.ryzenadj.policy"
if [ -f "$POLKIT_SRC" ]; then
  sudo cp "$POLKIT_SRC" "$POLKIT_DST"
  sudo chown root:root "$POLKIT_DST"
  sudo chmod 0644 "$POLKIT_DST"
  echo "   Política instalada. Opcional: sudo systemctl daemon-reload && sudo systemctl restart polkit"
else
  echo "   No se encontró política; omitiendo polkit."
fi

# [6/8] Acceso directo en el escritorio
echo "[6/8] Creando acceso directo en el escritorio..."
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

# [7/8] ryzenadj (control TDP)
echo "[7/8] Instalando ryzenadj (control TDP)..."
if command -v snap &>/dev/null; then
  if ! snap list ryzenadj &>/dev/null 2>&1; then
    sudo snap install ryzenadj --beta --devmode 2>/dev/null && echo "   ryzenadj instalado (snap)." || echo "   ryzenadj: no se pudo instalar por snap (instálalo manualmente: sudo snap install ryzenadj --beta --devmode)."
  else
    echo "   ryzenadj ya está instalado."
  fi
else
  echo "   Snap no está instalado; para control TDP instala ryzenadj manualmente (p. ej. desde fuentes)."
fi

# [8/8] nbfc (control ventilador) y arranque del servicio
echo "[8/8] Instalando nbfc (control ventilador)..."
if command -v nbfc &>/dev/null; then
  echo "   nbfc ya está instalado."
else
  if sudo apt-get install -y nbfc &>/dev/null 2>&1; then
    echo "   nbfc instalado desde los repos."
  else
    NBFC_DEB_URL="https://github.com/nbfc-linux/nbfc-linux/releases/download/0.3.19/nbfc-linux_0.3.19_amd64.deb"
    if command -v curl &>/dev/null; then
      if curl -sLf "$NBFC_DEB_URL" -o /tmp/nbfc-linux.deb 2>/dev/null; then
        sudo dpkg -i /tmp/nbfc-linux.deb 2>/dev/null && sudo apt-get install -f -y -qq 2>/dev/null && echo "   nbfc instalado desde nbfc-linux (GitHub)." || echo "   nbfc: no se pudo instalar el .deb."
        rm -f /tmp/nbfc-linux.deb
      else
        echo "   nbfc: descarga fallida; instálalo desde https://github.com/nbfc-linux/nbfc-linux/releases"
      fi
    else
      sudo apt-get install -y curl -qq 2>/dev/null || true
      if curl -sLf "$NBFC_DEB_URL" -o /tmp/nbfc-linux.deb 2>/dev/null; then
        sudo dpkg -i /tmp/nbfc-linux.deb 2>/dev/null && sudo apt-get install -f -y -qq 2>/dev/null && echo "   nbfc instalado desde nbfc-linux (GitHub)." || echo "   nbfc: no se pudo instalar el .deb."
        rm -f /tmp/nbfc-linux.deb
      else
        echo "   nbfc: instálalo desde https://github.com/nbfc-linux/nbfc-linux/releases"
      fi
    fi
  fi
fi
# Actualizar configs e intentar arrancar el servicio nbfc
if command -v nbfc &>/dev/null; then
  sudo nbfc update 2>/dev/null || true
  sudo systemctl enable nbfc_service 2>/dev/null || true
  (sudo nbfc config -s auto 2>/dev/null; sudo nbfc start 2>/dev/null) || true
  echo "   Servicio nbfc: enable al arranque; si no arranca, elige un perfil en la app (p. ej. Lenovo ThinkPad T14 Gen2)."
fi

echo ""
echo "=== Instalación completada ==="
echo "  Ejecutar la aplicación:"
echo "    $INSTALL_DIR/run-ryzen-master-commander.sh"
echo "  o usar el icono del escritorio."
echo ""
