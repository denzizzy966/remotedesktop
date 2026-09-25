#!/bin/bash
# ================================================================
#  UNINSTALLER LAN REMOTE DESKTOP - ADMIN SERVER (LINUX)
#  Target OS: Ubuntu 20.04/22.04/24.04 LTS, Linux Mint 20/21/22, Debian
#  Usage: sudo ./uninstall_admin_server.sh
# ================================================================

set -e

if [ "$EUID" -ne 0 ]; then
    echo "================================================================"
    echo " [ERROR] Harap jalankan uninstaller ini dengan izin sudo/root:"
    echo "         sudo ./uninstall_admin_server.sh"
    echo "================================================================"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "================================================================"
echo "  UNINSTALLER LAN REMOTE DESKTOP - ADMIN SERVER (LINUX)"
echo "================================================================"
echo ""
echo "Script ini akan:"
echo "  1. Menghentikan dan menghapus systemd background service"
echo "  2. Menghentikan proses server yang sedang aktif"
echo "  3. Menghapus aturan firewall UFW untuk port server"
echo "  4. Memberikan opsi pembersihan file data konfigurasi"
echo "================================================================"
echo ""

read -p "Apakah Anda yakin ingin mencopot pemasangan Admin Server? (Y/N, default Y): " CONFIRM
CONFIRM=${CONFIRM:-Y}
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo "[BATAL] Proses uninstalasi dibatalkan oleh pengguna."
    exit 0
fi

echo ""
echo "[1/4] Menghentikan dan menghapus Systemd Service..."
for SERVICE_NAME in "lan-remote-server.service" "lan-remotedesktop.service"; do
    if systemctl list-unit-files | grep -q "$SERVICE_NAME"; then
        echo "  - Menghentikan service $SERVICE_NAME..."
        systemctl stop "$SERVICE_NAME" || true
        systemctl disable "$SERVICE_NAME" || true
    fi
    if [ -f "/etc/systemd/system/$SERVICE_NAME" ]; then
        rm -f "/etc/systemd/system/$SERVICE_NAME"
        echo "  - File /etc/systemd/system/$SERVICE_NAME dihapus."
    fi
done

systemctl daemon-reload
systemctl reset-failed || true
echo "  - Layanan systemd berhasil dicopot."

echo ""
echo "[2/4] Menghentikan sisa proses server Python..."
pkill -f "run_server.py" || true
pkill -f "server.main:app" || true
echo "  - Proses server dipastikan nonaktif."

echo ""
echo "[3/4] Menghapus aturan firewall UFW..."
if command -v ufw >/dev/null 2>&1; then
    if ufw status | grep -q "Status: active"; then
        ufw delete allow 8001/tcp >/dev/null 2>&1 || true
        ufw delete allow 8000/tcp >/dev/null 2>&1 || true
        ufw delete allow 8002/udp >/dev/null 2>&1 || true
        echo "  - Aturan firewall untuk port 8001, 8000, dan 8002 berhasil dihapus dari UFW."
    else
        echo "  - Firewall UFW tidak aktif, tidak ada aturan yang perlu diubah."
    fi
else
    echo "  - UFW tidak terpasang."
fi

echo ""
echo "================================================================"
echo "  PEMBERSIHAN DATA DAN KONFIGURASI"
echo "================================================================"
echo "File data server mencakup password admin (config.json) dan"
echo "database alias/catatan perangkat (device_notes.json)."
read -p "Hapus file konfigurasi dan catatan perangkat? (Y/N, default N): " DEL_DATA
DEL_DATA=${DEL_DATA:-N}
if [[ "$DEL_DATA" =~ ^[Yy]$ ]]; then
    rm -f "$SCRIPT_DIR/server/config.json"
    rm -f "$SCRIPT_DIR/server/device_notes.json"
    echo "  - File konfigurasi dan catatan perangkat telah dihapus."
else
    echo "  - File konfigurasi dan catatan perangkat tetap dipertahankan."
fi

echo ""
echo "================================================================"
echo "  UNINSTALL ADMIN SERVER SELESAI DENGAN SUKSES!"
echo "================================================================"
echo "Layanan Admin Server telah sepenuhnya dihapus dari sistem Linux Anda."
echo "Folder project ini sekarang aman untuk dihapus jika tidak diperlukan."
echo "================================================================"
echo ""
