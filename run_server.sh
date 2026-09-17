#!/bin/bash
# LAN Remote Desktop - Server Launcher for Linux (Ubuntu / Linux Mint / Debian)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

python3 run_server.py "$@"
