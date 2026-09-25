#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="lan-remotedesktop-client"

echo "Menyalakan LAN Remote Desktop Client..."
if systemctl list-unit-files "${SERVICE_NAME}.service" >/dev/null 2>&1; then
    sudo systemctl restart "${SERVICE_NAME}.service"
    echo "Client service '${SERVICE_NAME}' berhasil dinyalakan via systemd!"
    echo "Cek status: sudo systemctl status ${SERVICE_NAME}"
else
    # Jalankan background proses
    nohup bash "$SCRIPT_DIR/run_client.sh" > "$SCRIPT_DIR/client.log" 2>&1 &
    sleep 1
    PID=$!
    echo "Client berhasil dijalankan di background (PID: $PID)!"
    echo "Log output tersimpan di: $SCRIPT_DIR/client.log"
fi
