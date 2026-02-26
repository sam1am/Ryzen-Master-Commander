#!/usr/bin/env bash
# Genera RyzenMasterCommander-bundle.tar.gz con solo los fuentes (sin Build/, sin .git, sin .venv).
# El instalador install-standalone.sh debe estar FUERA de este comprimido; se deja en Build/ para copiarlo aparte.
# Uso: desde la raíz del repositorio: ./Build/create-bundle.sh
# Resultado: RyzenMasterCommander-bundle.tar.gz en la raíz del repositorio.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT="$SCRIPT_DIR/RyzenMasterCommander-bundle.tar.gz"

cd "$REPO_ROOT"
echo "Creando comprimido (solo fuentes, sin Build/)..."
tar czf "$OUTPUT" \
  src bin polkit share tdp_profiles img \
  requirements.txt version.txt

echo "Creado: $OUTPUT"
echo ""
echo "Para distribuir: copia la carpeta Build/ completa al Ubuntu; dentro estarán"
echo "  install-standalone.sh y RyzenMasterCommander-bundle.tar.gz."
echo "  Luego: cd Build && chmod +x install-standalone.sh && ./install-standalone.sh"
echo ""
