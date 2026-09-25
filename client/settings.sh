#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ "$EUID" -eq 0 ]; then
    echo "================================================================"
    echo " [PERINGATAN] Jangan jalankan pengaturan dengan 'sudo'!"
    echo "================================================================"
    if [ -n "$SUDO_USER" ]; then
        exec sudo -u "$SUDO_USER" env DISPLAY="${DISPLAY:-:0}" XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}" DBUS_SESSION_BUS_ADDRESS="$DBUS_SESSION_BUS_ADDRESS" "$0" "$@"
    fi
fi

export DISPLAY="${DISPLAY:-:0}"
python3 client.py --settings
