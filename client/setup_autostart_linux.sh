#!/bin/bash
# Setup Autostart on Login/Boot for Linux Mint / Ubuntu

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Determine actual user home even if run with sudo
if [ -n "$SUDO_USER" ]; then
    USER_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)
    TARGET_USER="$SUDO_USER"
else
    USER_HOME="$HOME"
    TARGET_USER="$USER"
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
Comment=Background agent for LAN Remote Desktop & Fleet Monitoring
Icon=preferences-desktop-remote-desktop
Terminal=false
Categories=Network;Utility;
EOF

if [ -n "$SUDO_USER" ]; then
    chown -R "$SUDO_USER:$SUDO_USER" "$AUTOSTART_DIR"
fi

chmod +x "$DESKTOP_FILE"
chmod +x "$SCRIPT_DIR/run_client.sh"

echo "=========================================================="
echo " [SUCCESS] Autostart Startup Berhasil Dikonfigurasi!"
echo " User Target : $TARGET_USER"
echo " Lokasi File : $DESKTOP_FILE"
echo ""
echo " Client akan otomatis menyala di latar belakang dan"
echo " memunculkan ikon System Tray setiap kali user login."
echo "=========================================================="
