#!/bin/bash
SERVICE_NAME="lan-remotedesktop-client"

echo "Menghentikan LAN Remote Desktop Client..."
if systemctl is-active --quiet "${SERVICE_NAME}.service" 2>/dev/null; then
    sudo systemctl stop "${SERVICE_NAME}.service"
    echo "Service '${SERVICE_NAME}' berhasil dihentikan."
fi

# Pastikan proses background juga dihentikan
pkill -f "python3.*client\.py" || true
echo "Seluruh proses client telah dihentikan."
