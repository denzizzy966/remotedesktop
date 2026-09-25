#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================================"
echo " Downloading Client PIP Packages for Offline Installation..."
echo " Target Folder: $SCRIPT_DIR/offline_packages"
echo "================================================================"

mkdir -p "$SCRIPT_DIR/offline_packages"

pip3 download -r "$SCRIPT_DIR/requirements.txt" python-xlib -d "$SCRIPT_DIR/offline_packages"

echo "Selesai! Seluruh wheel disimpan di $SCRIPT_DIR/offline_packages"
