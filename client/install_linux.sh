#!/bin/bash
# ================================================================
#  INSTALLER LAN REMOTE DESKTOP - CLIENT AGENT
#  Target OS: Ubuntu 22.04 LTS / Linux Mint 22 (X11 / Xorg)
# ================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=========================================================="
echo " INSTALLER LAN REMOTE DESKTOP - CLIENT AGENT (LINUX)"
echo " Target OS: Ubuntu 22.04 LTS / Linux Mint 22"
echo "=========================================================="
echo ""

# Helper to wait if Ubuntu background auto-updates (unattended-upgrades) is holding the lock
wait_for_apt_lock() {
    local waited=0
    while sudo fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1 || sudo fuser /var/lib/apt/lists/lock >/dev/null 2>&1 || pgrep -f "unattended-upgr" >/dev/null 2>&1; do
        if [ $waited -eq 0 ]; then
            echo "[INFO] Ubuntu sedang menjalankan update sistem di latar belakang (unattended-upgrades)."
            echo "       Menunggu proses selesai dan lock dpkg dilepaskan secara aman..."
        fi
        sleep 3
        waited=$((waited + 3))
        if [ $waited -ge 45 ]; then
            echo "[INFO] Menghentikan service background update agar instalasi dapat dilanjutkan..."
            sudo systemctl stop unattended-upgrades >/dev/null 2>&1 || true
            sleep 2
            break
        fi
    done
}

# 1. Update apt & install system packages (Hanya jika belum terpasang)
if command -v python3 >/dev/null 2>&1 && command -v pip3 >/dev/null 2>&1 && python3 -c "import tkinter, gi" >/dev/null 2>&1; then
    echo "[1/6] Python 3, pip3, dan modul antarmuka sistem sudah terpasang ($(python3 --version))."
else
    echo "[1/6] Memasang paket dependensi sistem (Python, Tkinter, AppIndicator)..."
    wait_for_apt_lock
    sudo apt-get update -o Acquire::ForceIPv4=true || true
    wait_for_apt_lock
    sudo apt-get install -y \
        python3 \
        python3-pip \
        python3-dev \
        python3-tk \
        python3-pil \
        python3-gi \
        python3-gi-cairo \
        gir1.2-ayatanaappindicator3-0.1 \
        gir1.2-appindicator3-0.1 \
        gir1.2-gtk-3.0 \
        libayatana-appindicator3-1 \
        scrot \
        libx11-dev \
        libxtst-dev \
        libpng-dev \
        x11-xserver-utils || true
fi

echo ""
python3 -c "import sys; print('Python terdeteksi:', sys.version.split()[0])"
echo ""

# 2. Install pip requirements (Offline or Online)
echo "[2/6] Memasang pustaka Python client..."
if [ -d "$SCRIPT_DIR/offline_packages" ]; then
    echo "[OFFLINE MODE] Folder 'client/offline_packages' terdeteksi!"
    echo "Memasang dependensi client langsung dari cache lokal (tanpa perlu koneksi internet)..."
    pip3 install --no-index --find-links="$SCRIPT_DIR/offline_packages" -r "$SCRIPT_DIR/requirements.txt" || \
    pip3 install --no-index --find-links="$SCRIPT_DIR/offline_packages" --break-system-packages -r "$SCRIPT_DIR/requirements.txt" || \
    pip3 install -r "$SCRIPT_DIR/requirements.txt" || pip3 install --break-system-packages -r "$SCRIPT_DIR/requirements.txt"
elif [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    pip3 install -r "$SCRIPT_DIR/requirements.txt" || pip3 install --break-system-packages -r "$SCRIPT_DIR/requirements.txt"
elif [ -f "$ROOT_DIR/requirements.txt" ]; then
    pip3 install -r "$ROOT_DIR/requirements.txt" || pip3 install --break-system-packages -r "$ROOT_DIR/requirements.txt"
else
    pip3 install websockets psutil mss pillow pynput pyautogui pyperclip requests pystray || pip3 install --break-system-packages websockets psutil mss pillow pynput pyautogui pyperclip requests pystray
fi
echo "Dependensi client berhasil dipasang!"
echo ""

# 3. Konfigurasi Koneksi Server Admin
echo "[3/6] Konfigurasi Koneksi Server Admin..."
echo "Secara bawaan, client akan otomatis mencari Server di LAN via UDP beacon."
read -p "Masukkan IP Server Admin (kosongkan jika ingin Auto-Discovery): " TARGET_IP
if [ -n "$TARGET_IP" ]; then
    read -p "Masukkan Port Server Admin (default 8001): " TARGET_PORT
    TARGET_PORT=${TARGET_PORT:-8001}
    cat << EOF > "$SCRIPT_DIR/config.json"
{
    "server_url": "",
    "server_ip": "$TARGET_IP",
    "server_port": $TARGET_PORT,
    "device_id": "",
    "auto_discover": false
}
EOF
    echo "Konfigurasi disimpan: Server IP = $TARGET_IP, Port = $TARGET_PORT"
else
    cat << EOF > "$SCRIPT_DIR/config.json"
{
    "server_url": "",
    "server_ip": "",
    "server_port": 8001,
    "device_id": "",
    "auto_discover": true
}
EOF
    echo "Mode Auto-Discovery aktif."
fi
echo ""

# 4. Buat runner script client & settings
echo "[4/6] Menyiapkan launcher script..."
chmod +x "$SCRIPT_DIR/run_client.sh" "$SCRIPT_DIR/settings.sh" "$SCRIPT_DIR/status_client.sh" "$SCRIPT_DIR/start_client.sh" "$SCRIPT_DIR/stop_client.sh" "$SCRIPT_DIR/install_client_service.sh" "$SCRIPT_DIR/uninstall_client_service.sh" 2>/dev/null || true

# 5. Pasang Shortcut Desktop & Menu Aplikasi
echo "[5/6] Memasang Shortcut di Desktop dan Menu Aplikasi Linux..."
if [ -n "$SUDO_USER" ]; then
    USER_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)
    DESKTOP_OWNER="$SUDO_USER"
else
    USER_HOME="$HOME"
    DESKTOP_OWNER="$USER"
fi

AUTOSTART_DIR="$USER_HOME/.config/autostart"
APPS_DIR="$USER_HOME/.local/share/applications"
DESKTOP_DIR="$USER_HOME/Desktop"
mkdir -p "$AUTOSTART_DIR" "$APPS_DIR" "$DESKTOP_DIR"

# 5.A Shortcut Client
CLIENT_DESKTOP_CONTENT="[Desktop Entry]
Type=Application
Exec=$SCRIPT_DIR/run_client.sh
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=LAN Remote Desktop Client
Comment=Background agent for LAN Remote Desktop & Monitoring
Icon=preferences-desktop-remote-desktop
Terminal=false
Categories=Network;Utility;
"

echo "$CLIENT_DESKTOP_CONTENT" > "$AUTOSTART_DIR/lan-remotedesktop-client.desktop"
echo "$CLIENT_DESKTOP_CONTENT" > "$APPS_DIR/lan-remotedesktop-client.desktop"
echo "$CLIENT_DESKTOP_CONTENT" > "$DESKTOP_DIR/lan-remotedesktop-client.desktop"

# 5.B Shortcut Pengaturan Server (Ganti IP GUI)
SETTINGS_DESKTOP_CONTENT="[Desktop Entry]
Type=Application
Exec=$SCRIPT_DIR/settings.sh
Hidden=false
NoDisplay=false
Name=Pengaturan Server LAN Remote
Comment=Ganti IP dan Port Server Admin LAN Remote Desktop
Icon=preferences-system-network
Terminal=false
Categories=Network;Settings;
"

echo "$SETTINGS_DESKTOP_CONTENT" > "$APPS_DIR/lan-remotedesktop-settings.desktop"
echo "$SETTINGS_DESKTOP_CONTENT" > "$DESKTOP_DIR/lan-remotedesktop-settings.desktop"

# Set permissions
chmod +x "$AUTOSTART_DIR/lan-remotedesktop-client.desktop" "$APPS_DIR/lan-remotedesktop-client.desktop" "$DESKTOP_DIR/lan-remotedesktop-client.desktop" 2>/dev/null || true
chmod +x "$APPS_DIR/lan-remotedesktop-settings.desktop" "$DESKTOP_DIR/lan-remotedesktop-settings.desktop" 2>/dev/null || true

# Mark desktop file trusted if gio is present
if command -v gio >/dev/null 2>&1; then
    gio set "$DESKTOP_DIR/lan-remotedesktop-client.desktop" metadata::trusted true 2>/dev/null || true
    gio set "$DESKTOP_DIR/lan-remotedesktop-settings.desktop" metadata::trusted true 2>/dev/null || true
fi

if [ -n "$SUDO_USER" ]; then
    chown -R "$DESKTOP_OWNER:$DESKTOP_OWNER" "$AUTOSTART_DIR" "$APPS_DIR" "$DESKTOP_DIR" 2>/dev/null || true
fi

# 6. Opsi Pasang sebagai Systemd Service
echo ""
echo "[6/6] Aktivasi Layanan Background Service..."
echo "PILIHAN MODE MENJALANKAN CLIENT:"
echo " 1. SYSTEMD SERVICE (Direkomendasikan): Berjalan otomatis 24/7 di background dan saat boot."
echo " 2. DESKTOP AUTOSTART: Berjalan di background setiap kali user login ke desktop."
echo ""
read -p "Pasang sebagai Systemd Service sekarang? (Y/n, default: Y): " INSTALL_SERVICE_CHOICE
INSTALL_SERVICE_CHOICE=${INSTALL_SERVICE_CHOICE:-Y}

if [[ "$INSTALL_SERVICE_CHOICE" =~ ^[Yy]$ ]]; then
    echo "Menyiapkan systemd service..."
    bash "$SCRIPT_DIR/install_client_service.sh"
    # Hapus desktop autostart agar tidak berjalan ganda saat user login ke desktop
    rm -f "$AUTOSTART_DIR/lan-remotedesktop-client.desktop" 2>/dev/null || true
else
    echo "Memulai client di latar belakang..."
    bash "$SCRIPT_DIR/start_client.sh"
fi

echo ""
echo "=========================================================="
echo "          INSTALASI CLIENT LINUX SELESAI!"
echo "=========================================================="
echo ""
echo " 📋 INFORMASI STATUS & LAYANAN YANG BERJALAN:"
echo "  - Nama Systemctl Service : lan-remotedesktop-client"
echo "  - Cek Status Service     : sudo systemctl status lan-remotedesktop-client"
echo "  - Cek Status Cepat (CLI) : ./client/status_client.sh"
echo "  - Cek Log Realtime       : sudo journalctl -u lan-remotedesktop-client -f"
echo ""
echo " 🖥️ PENGATURAN GANTI IP SERVER (GUI):"
echo "  - Dobel klik shortcut 'Pengaturan Server LAN Remote' di Desktop Anda!"
echo "  - Atau dari terminal jalankan: ./client/settings.sh"
echo ""
echo "  - Untuk menghentikan client : ./client/stop_client.sh"
echo "  - Untuk menyalakan kembali  : ./client/start_client.sh"
echo "=========================================================="
echo ""
