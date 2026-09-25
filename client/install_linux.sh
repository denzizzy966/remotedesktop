#!/bin/bash
# Installer for Ubuntu 22.04 LTS / Linux Mint 22


echo "=========================================================="
echo " Installing LAN Remote Desktop Client for Linux"
echo " (Ubuntu 22.04 LTS / Linux Mint 22)"
echo "=========================================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "[1/4] Updating system packages & installing required system dependencies..."
sudo apt-get update -o Acquire::ForceIPv4=true || true
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
    scrot \
    libx11-dev \
    libxtst-dev \
    libpng-dev \
    x11-xserver-utils || true

echo "[2/4] Installing Python requirements..."
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    REQ_FILE="$SCRIPT_DIR/requirements.txt"
elif [ -f "$ROOT_DIR/requirements.txt" ]; then
    REQ_FILE="$ROOT_DIR/requirements.txt"
else
    REQ_FILE=""
fi

if [ -n "$REQ_FILE" ]; then
    pip3 install -r "$REQ_FILE" || pip3 install --break-system-packages -r "$REQ_FILE"
else
    pip3 install websockets psutil mss pillow pynput pyautogui pyperclip requests pystray || pip3 install --break-system-packages websockets psutil mss pillow pynput pyautogui pyperclip requests pystray
fi

echo "[3/5] Konfigurasi Koneksi Server Admin..."
echo "Secara bawaan, client akan otomatis mencari Server di LAN via UDP."
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

echo "[4/5] Creating client launcher script..."
cat << 'EOF' > "$SCRIPT_DIR/run_client.sh"
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ "$EUID" -eq 0 ]; then
    echo "================================================================"
    echo " [PERINGATAN] Jangan jalankan client agent dengan 'sudo'!"
    echo "  System Tray dan antarmuka GUI memerlukan akses ke sesi desktop"
    echo "  pengguna biasa (X11 & DBus)."
    echo "================================================================"
    if [ -n "$SUDO_USER" ]; then
        echo "Beralih otomatis ke user '$SUDO_USER'..."
        exec sudo -u "$SUDO_USER" env DISPLAY="${DISPLAY:-:0}" XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}" DBUS_SESSION_BUS_ADDRESS="$DBUS_SESSION_BUS_ADDRESS" "$0" "$@"
    fi
fi

# Ensure DISPLAY is set for X11 screen capture
export DISPLAY="${DISPLAY:-:0}"
python3 client.py "$@"
EOF
chmod +x "$SCRIPT_DIR/run_client.sh"

echo "[5/5] Setting up Desktop Autostart entry (optional)..."
if [ -n "$SUDO_USER" ]; then
    USER_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)
else
    USER_HOME="$HOME"
fi

AUTOSTART_DIR="$USER_HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"

DESKTOP_FILE="$AUTOSTART_DIR/lan-remotedesktop-client.desktop"
cat << EOF > "$DESKTOP_FILE"
[Desktop Entry]
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
EOF

if [ -n "$SUDO_USER" ]; then
    chown -R "$SUDO_USER:$SUDO_USER" "$AUTOSTART_DIR"
fi
chmod +x "$DESKTOP_FILE"

echo ""
echo "=========================================================="
echo " Installation Complete!"
echo " To start the client manually, run:"
echo "   $SCRIPT_DIR/run_client.sh"
echo ""
echo " Note for Ubuntu: Please ensure you are logged into an"
echo " 'Xorg' session (select Ubuntu on Xorg on the login gear icon)"
echo " for full remote screen capture and mouse/keyboard injection."
echo " Linux Mint 22 Cinnamon uses X11 by default."
echo "=========================================================="
