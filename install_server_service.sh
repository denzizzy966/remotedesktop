#!/bin/bash
# ================================================================
#  Install LAN Remote Desktop Server as a Linux Systemd Service
#  Usage: sudo ./install_server_service.sh
# ================================================================

set -e

if [ "$EUID" -ne 0 ]; then
    echo "================================================================"
    echo " [ERROR] Harap jalankan script ini dengan hak akses sudo/root:"
    echo "         sudo ./install_server_service.sh"
    echo "================================================================"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACTUAL_USER="${SUDO_USER:-$(logname 2>/dev/null || echo $USER)}"

# Detect python executable
PYTHON_PATH="$(which python3)"
if [ -z "$PYTHON_PATH" ]; then
    echo "[ERROR] python3 tidak ditemukan di sistem. Harap pasang python3 terlebih dahulu."
    exit 1
fi

echo "================================================================"
echo "  Memasang LAN Remote Server sebagai Systemd Service"
echo "  User            : $ACTUAL_USER"
echo "  Working Dir     : $SCRIPT_DIR"
echo "  Python Exec     : $PYTHON_PATH"
echo "================================================================"

SERVICE_FILE="/etc/systemd/system/lan-remote-server.service"

cat << EOF > "$SERVICE_FILE"
[Unit]
Description=LAN Remote Desktop & Fleet Monitoring Server
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$ACTUAL_USER
WorkingDirectory=$SCRIPT_DIR
ExecStart=$PYTHON_PATH $SCRIPT_DIR/run_server.py
Restart=always
RestartSec=5
LimitNOFILE=65536
Environment=PYTHONUNBUFFERED=1
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

chmod 644 "$SERVICE_FILE"

echo "[1/3] Memperbarui systemd daemon..."
systemctl daemon-reload

echo "[2/3] Mengaktifkan autostart saat booting..."
systemctl enable lan-remote-server.service

echo "[3/3] Menjalankan service sekarang..."
systemctl restart lan-remote-server.service

# Setup firewall if UFW is active
if command -v ufw >/dev/null 2>&1; then
    if ufw status | grep -q "Status: active"; then
        echo ""
        echo "[Firewall] Membuka port di UFW..."
        ufw allow 8001/tcp comment "LAN Remote Desktop Web Admin"
        ufw allow 8000/tcp comment "LAN Remote Desktop Fallback"
        ufw allow 8002/udp comment "LAN Remote Desktop UDP Discovery"
        echo "[Firewall] Port 8001/tcp, 8000/tcp, dan 8002/udp dibuka."
    fi
fi

echo ""
echo "================================================================"
echo "  SUCCESS! Service Server Berhasil Dipasang & Berjalan"
echo "================================================================"
echo "Perintah manajemen service:"
echo "  - Cek Status   : sudo systemctl status lan-remote-server"
echo "  - Cek Log      : sudo journalctl -u lan-remote-server -f"
echo "  - Restart      : sudo systemctl restart lan-remote-server"
echo "  - Berhenti     : sudo systemctl stop lan-remote-server"
echo "  - Hapus Service: sudo ./uninstall_server_service.sh"
echo "================================================================"
echo ""
systemctl status lan-remote-server.service --no-pager
