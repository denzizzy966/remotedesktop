#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Warn if running as root / sudo
if [ "$EUID" -eq 0 ]; then
    echo "================================================================"
    echo " [PERINGATAN] Jangan jalankan client agent dengan 'sudo'!"
    echo "  System Tray dan antarmuka GUI memerlukan akses ke sesi desktop"
    echo "  pengguna biasa (X11 & DBus)."
    echo "================================================================"
    if [ -n "$SUDO_USER" ]; then
        REAL_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)
        REAL_UID=$(id -u "$SUDO_USER" 2>/dev/null || echo 1000)
        echo "Beralih otomatis ke user '$SUDO_USER'..."
        exec sudo -u "$SUDO_USER" env DISPLAY="${DISPLAY:-:0}" XAUTHORITY="${REAL_HOME}/.Xauthority" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/${REAL_UID}/bus" PYSTRAY_BACKEND="appindicator" "$0" "$@"
    fi
fi

# Ensure DISPLAY and common variables are set for X11 screen capture
export DISPLAY="${DISPLAY:-:0}"
if [ -z "$XAUTHORITY" ] && [ -f "$HOME/.Xauthority" ]; then
    export XAUTHORITY="$HOME/.Xauthority"
fi
export PYSTRAY_BACKEND="${PYSTRAY_BACKEND:-appindicator}"

python3 "$SCRIPT_DIR/client.py" "$@"
