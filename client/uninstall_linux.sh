#!/bin/bash
# ================================================================
#  UNINSTALLER LAN REMOTE DESKTOP - CLIENT AGENT (LINUX)
#  Target OS: Ubuntu 20.04/22.04/24.04 LTS, Linux Mint 20/21/22, Debian
#  Usage: ./uninstall_linux.sh (atau sudo ./uninstall_linux.sh)
# ================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Detect user home directory
if [ -n "$SUDO_USER" ]; then
    TARGET_USER="$SUDO_USER"
    USER_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)
else
    TARGET_USER="$USER"
    USER_HOME="$HOME"
fi

echo "================================================================"
echo "  UNINSTALLER LAN REMOTE DESKTOP - CLIENT AGENT (LINUX)"
echo "  User: $TARGET_USER ($USER_HOME)"
echo "================================================================"
echo ""
echo "Script ini akan:"
echo "  1. Menghentikan proses Client Agent yang sedang berjalan"
echo "  2. Menghapus entri Autostart desktop (~/.config/autostart)"
echo "  3. Menghapus background systemd service (jika ada)"
echo "  4. Memberikan opsi pembersihan konfigurasi client (config.json)"
echo "================================================================"
echo ""

read -p "Apakah Anda yakin ingin mencopot Client Agent dari sistem ini? (Y/N, default Y): " CONFIRM
CONFIRM=${CONFIRM:-Y}
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo "[BATAL] Proses uninstalasi dibatalkan oleh pengguna."
    exit 0
fi

echo ""
echo "[1/3] Menghentikan proses Client Agent..."
pkill -f "python3 client.py" || true
pkill -f "run_client.sh" || true
echo "  - Proses client agent berhasil dihentikan."

echo ""
echo "[2/3] Menghapus pendaftaran Autostart Desktop..."
AUTOSTART_FILE="$USER_HOME/.config/autostart/lan-remotedesktop-client.desktop"
if [ -f "$AUTOSTART_FILE" ]; then
    rm -f "$AUTOSTART_FILE"
    echo "  - File autostart $AUTOSTART_FILE berhasil dihapus."
else
    echo "  - File autostart desktop tidak ditemukan (sudah bersih)."
fi

# Also check root autostart if different
if [ "$USER_HOME" != "$HOME" ] && [ -f "$HOME/.config/autostart/lan-remotedesktop-client.desktop" ]; then
    rm -f "$HOME/.config/autostart/lan-remotedesktop-client.desktop"
fi

# Check systemd client service if installed
if [ -f "/etc/systemd/system/lan-remote-client.service" ]; then
    echo "  - Menghapus service /etc/systemd/system/lan-remote-client.service..."
    if [ "$EUID" -eq 0 ]; then
        systemctl stop lan-remote-client.service || true
        systemctl disable lan-remote-client.service || true
        rm -f "/etc/systemd/system/lan-remote-client.service"
        systemctl daemon-reload
    else
        sudo systemctl stop lan-remote-client.service || true
        sudo systemctl disable lan-remote-client.service || true
        sudo rm -f "/etc/systemd/system/lan-remote-client.service"
        sudo systemctl daemon-reload
    fi
fi

echo ""
echo "[3/3] Pembersihan file konfigurasi..."
read -p "Hapus file konfigurasi client (config.json)? (Y/N, default N): " DEL_CONFIG
DEL_CONFIG=${DEL_CONFIG:-N}
if [[ "$DEL_CONFIG" =~ ^[Yy]$ ]]; then
    rm -f "$SCRIPT_DIR/config.json"
    echo "  - File config.json telah dihapus."
else
    echo "  - File config.json tetap dipertahankan."
fi

echo ""
echo "================================================================"
echo "  UNINSTALL CLIENT AGENT SELESAI DENGAN SUKSES!"
echo "================================================================"
echo "Client Agent telah sepenuhnya dicopot dari komputer ini."
echo "PC ini tidak lagi terhubung atau memancarkan layar ke Server Admin."
echo "================================================================"
echo ""
