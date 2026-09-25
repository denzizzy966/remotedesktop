#!/bin/bash
# ================================================================
#  UNINSTALLER SYSTEMD SERVICE - LAN REMOTE DESKTOP CLIENT
# ================================================================

set -e

SERVICE_NAME="lan-remotedesktop-client"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo "================================================================"
echo "  MENGHAPUS SYSTEMD SERVICE LAN REMOTE DESKTOP CLIENT"
echo "================================================================"
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "[INFO] Skrip memerlukan hak akses root."
    exec sudo bash "$0" "$@"
fi

if [ -f "$SERVICE_FILE" ]; then
    echo "[1/3] Menghentikan service..."
    systemctl stop "${SERVICE_NAME}.service" || true
    echo "[2/3] Menonaktifkan autostart systemd..."
    systemctl disable "${SERVICE_NAME}.service" || true
    echo "[3/3] Menghapus file unit $SERVICE_FILE..."
    rm -f "$SERVICE_FILE"
    systemctl daemon-reload
    echo ""
    echo "[BERHASIL] Service '${SERVICE_NAME}' telah dihapus dari sistem."
else
    echo "[INFO] Service '${SERVICE_NAME}' tidak ditemukan terpasang."
fi
echo "================================================================"
