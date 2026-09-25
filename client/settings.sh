#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ "$EUID" -eq 0 ]; then
    if [ -n "$SUDO_USER" ]; then
        REAL_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)
        REAL_UID=$(id -u "$SUDO_USER" 2>/dev/null || echo 1000)
        exec sudo -u "$SUDO_USER" env DISPLAY="${DISPLAY:-:0}" XAUTHORITY="${REAL_HOME}/.Xauthority" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/${REAL_UID}/bus" "$0" "$@"
    fi
fi

# Ensure GUI display variables
export DISPLAY="${DISPLAY:-:0}"
if [ -z "$XAUTHORITY" ] && [ -f "$HOME/.Xauthority" ]; then
    export XAUTHORITY="$HOME/.Xauthority"
fi

python3 "$SCRIPT_DIR/client.py" --settings
