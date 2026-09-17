#!/bin/bash
# ================================================================
#  INSTALLER LAN REMOTE DESKTOP - ADMIN SERVER (LINUX)
#  Target OS: Ubuntu 20.04/22.04 LTS, Linux Mint 20/21/22, Debian
# ================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURRENT_USER="$(logname 2>/dev/null || echo $USER)"

echo "================================================================"
echo "  INSTALLER LAN REMOTE DESKTOP - ADMIN SERVER"
echo "  Target: Linux (Ubuntu / Linux Mint / Debian)"
echo "================================================================"
echo ""

# 1. Update apt & install Python
echo "[1/4] Memasang Python & paket sistem..."
sudo apt-get update
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    libffi-dev

echo ""
python3 -c "import sys; print('Python terdeteksi:', sys.version.split()[0])"
echo ""

# 2. Install pip requirements
echo "[2/4] Memasang dependensi server (FastAPI, Uvicorn, WebSockets, psutil)..."
cd "$SCRIPT_DIR"
pip3 install -r requirements.txt || pip3 install --break-system-packages -r requirements.txt
echo "Dependensi server berhasil dipasang!"
echo ""

# 3. Setup Admin Password
echo "[3/4] Pengaturan Password Admin..."
echo "Anda dapat mengatur password admin sekarang melalui console,"
echo "atau mengaturnya saat pertama kali membuka web browser."
echo ""
read -p "Ingin mengatur password admin sekarang? (Y/N, default Y): " SETUP_PASS
SETUP_PASS=${SETUP_PASS:-Y}
if [[ "$SETUP_PASS" =~ ^[Yy]$ ]]; then
    python3 "$SCRIPT_DIR/reset_password.py"
fi
echo ""

# 4. Optional: Setup systemd background service
echo "[4/4] Konfigurasi Systemd Background Service..."
echo "Apakah Anda ingin server ini berjalan otomatis di background (24/7)"
echo "setiap kali komputer/server Linux booting?"
read -p "Pasang sebagai systemd service? (Y/N, default Y): " INSTALL_SERVICE
INSTALL_SERVICE=${INSTALL_SERVICE:-Y}

if [[ "$INSTALL_SERVICE" =~ ^[Yy]$ ]]; then
    SERVICE_FILE="/etc/systemd/system/lan-remote-server.service"
    PYTHON_PATH="$(which python3)"

    sudo bash -c "cat << EOF > $SERVICE_FILE
[Unit]
Description=LAN Remote Desktop & Fleet Monitoring Server
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$SCRIPT_DIR
ExecStart=$PYTHON_PATH $SCRIPT_DIR/run_server.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF"

    sudo systemctl daemon-reload
    sudo systemctl enable lan-remote-server.service
    sudo systemctl restart lan-remote-server.service
    echo "Service 'lan-remote-server' berhasil dipasang dan dijalankan!"
    echo "Status service dapat dicek via: sudo systemctl status lan-remote-server"
fi

# 5. Firewall configuration (UFW if active)
if command -v ufw >/dev/null 2>&1; then
    if sudo ufw status | grep -q "Status: active"; then
        echo ""
        echo "Mengizinkan port di firewall UFW..."
        sudo ufw allow 8001/tcp comment "LAN Remote Desktop Web"
        sudo ufw allow 8000/tcp comment "LAN Remote Desktop Web Fallback"
        sudo ufw allow 8002/udp comment "LAN Remote Desktop Discovery"
        echo "Port firewall UFW berhasil dibuka."
    fi
fi

chmod +x "$SCRIPT_DIR/run_server.sh" "$SCRIPT_DIR/reset_password.sh"

echo ""
echo "================================================================"
echo "  INSTALASI SERVER ADMIN DI LINUX SELESAI!"
echo "================================================================"
echo "Jika tidak menggunakan systemd, Anda dapat menjalankan manual via:"
echo "   ./run_server.sh"
echo ""
echo "Dashboard dapat diakses di browser melalui:"
echo "   http://localhost:8001 (atau http://<IP_SERVER>:8001)"
echo "Jika lupa password di kemudian hari, jalankan:"
echo "   ./reset_password.sh"
echo "================================================================"
echo ""
