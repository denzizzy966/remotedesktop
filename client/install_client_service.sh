#!/bin/bash
# ================================================================
#  INSTALLER SYSTEMD SERVICE - LAN REMOTE DESKTOP CLIENT
#  Target: Linux (Ubuntu / Linux Mint / Debian)
# ================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="lan-remotedesktop-client"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo "================================================================"
echo "  MEMASANG CLIENT SEBAGAI SYSTEMD BACKGROUND SERVICE (24/7)"
echo "  Target Service: ${SERVICE_NAME}.service"
echo "================================================================"
echo ""

# 1. Pastikan script dijalankan dengan sudo / root
if [ "$EUID" -ne 0 ]; then
    echo "[INFO] Skrip memerlukan hak akses root untuk mendaftarkan systemd service."
    echo "       Mencoba menjalankan dengan sudo..."
    exec sudo bash "$0" "$@"
fi

# 2. Deteksi user desktop aktif (bukan root)
ACTUAL_USER="${SUDO_USER:-$USER}"
if [ "$ACTUAL_USER" = "root" ]; then
    # Cari user non-root pertama yang sedang login di desktop
    LOGGED_IN=$(who | awk '{print $1}' | grep -v 'root' | head -n1 || true)
    if [ -n "$LOGGED_IN" ]; then
        ACTUAL_USER="$LOGGED_IN"
    else
        ACTUAL_USER=$(awk -F: '$3 >= 1000 && $3 < 60000 {print $1}' /etc/passwd | head -n1 || echo "root")
    fi
fi

ACTUAL_HOME=$(getent passwd "$ACTUAL_USER" | cut -d: -f6)
ACTUAL_UID=$(id -u "$ACTUAL_USER" 2>/dev/null || echo 1000)
PYTHON_BIN=$(which python3 || echo "/usr/bin/python3")

echo "[1/4] User desktop terdeteksi : $ACTUAL_USER (UID: $ACTUAL_UID, Home: $ACTUAL_HOME)"
echo "[2/4] Lokasi client           : $SCRIPT_DIR/client.py"
echo "[3/4] Python executable       : $PYTHON_BIN"
echo ""

# 3. Buat file systemd service
echo "[4/4] Mendaftarkan unit systemd ke $SERVICE_FILE..."
cat << EOF > "$SERVICE_FILE"
[Unit]
Description=LAN Remote Desktop Client Agent
After=network.target graphical.target systemd-user-sessions.service
Wants=graphical.target

[Service]
Type=simple
User=$ACTUAL_USER
WorkingDirectory=$SCRIPT_DIR
Environment=DISPLAY=:0
Environment=XAUTHORITY=$ACTUAL_HOME/.Xauthority
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$ACTUAL_UID/bus
Environment=PYSTRAY_BACKEND=appindicator
Environment=PYTHONUNBUFFERED=1
ExecStart=$PYTHON_BIN $SCRIPT_DIR/client.py
Restart=always
RestartSec=3

[Install]
WantedBy=graphical.target
EOF

# Pastikan kepemilikan folder client dimiliki oleh user
chown -R "$ACTUAL_USER:$ACTUAL_USER" "$SCRIPT_DIR"

# 4. Aktifkan & nyalakan service
systemctl daemon-reload
systemctl enable "${SERVICE_NAME}.service"
systemctl restart "${SERVICE_NAME}.service"

echo ""
echo "================================================================"
echo " [BERHASIL] Client Service '${SERVICE_NAME}' Berhasil Aktif!"
echo "================================================================"
echo ""
echo " Status Service Sekarang:"
systemctl status "${SERVICE_NAME}.service" --no-pager || true
echo ""
echo " Perintah Manajemen Service di Terminal Linux:"
echo " ---------------------------------------------------------------"
echo "  - Cek Status : sudo systemctl status ${SERVICE_NAME}"
echo "  - Cek Log    : sudo journalctl -u ${SERVICE_NAME} -f"
echo "  - Restart    : sudo systemctl restart ${SERVICE_NAME}"
echo "  - Hentikan   : sudo systemctl stop ${SERVICE_NAME}"
echo "  - Hapus      : sudo ./client/uninstall_client_service.sh"
echo " ---------------------------------------------------------------"
echo " Untuk membuka GUI Ganti IP Server kapan saja:"
echo "   $SCRIPT_DIR/settings.sh (atau double-click di Desktop)"
echo "================================================================"
echo ""
