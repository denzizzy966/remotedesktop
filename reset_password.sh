#!/bin/bash
# LAN Remote Desktop - Console Password Reset for Linux
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

python3 reset_password.py "$@"
