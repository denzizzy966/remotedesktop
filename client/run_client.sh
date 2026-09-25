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
        echo "Beralih otomatis ke user '$SUDO_USER'..."
        exec sudo -u "$SUDO_USER" env DISPLAY="${DISPLAY:-:0}" XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}" DBUS_SESSION_BUS_ADDRESS="$DBUS_SESSION_BUS_ADDRESS" "$0" "$@"
    fi
fi

# Ensure DISPLAY and common variables are set for X11 screen capture
export DISPLAY="${DISPLAY:-:0}"
python3 client.py "$@"
