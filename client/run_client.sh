#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
# Ensure DISPLAY is set for X11 screen capture
export DISPLAY="${DISPLAY:-:0}"
python3 client.py "$@"
