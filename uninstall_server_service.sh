#!/bin/bash
# ================================================================
#  Uninstall LAN Remote Desktop Server Linux Systemd Service
#  Usage: sudo ./uninstall_server_service.sh
# ================================================================

set -e

if [ "$EUID" -ne 0 ]; then
    echo "================================================================"
    echo " [ERROR] Harap jalankan script ini dengan hak akses sudo/root:"
    echo "         sudo ./uninstall_server_service.sh"
    echo "================================================================"
    exit 1
fi

SERVICE_FILE="/etc/systemd/system/lan-remote-server.service"

echo "================================================================"
echo "  Menghapus LAN Remote Server Systemd Service"
echo "================================================================"

if [ -f "$SERVICE_FILE" ]; then
    echo "[1/3] Menghentikan service..."
    systemctl stop lan-remote-server.service || true

    echo "[2/3] Menonaktifkan autostart..."
    systemctl disable lan-remote-server.service || true

    echo "[3/3] Menghapus file service..."
    rm -f "$SERVICE_FILE"
    systemctl daemon-reload
    systemctl reset-failed || true

    echo ""
    echo "Service lan-remote-server berhasil dicopot dari sistem."
else
    echo "Service file $SERVICE_FILE tidak ditemukan."
fi
