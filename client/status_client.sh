#!/bin/bash
# ================================================================
#  STATUS CHECKER - LAN REMOTE DESKTOP CLIENT
# ================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="lan-remotedesktop-client"

echo "================================================================"
echo "      STATUS PENGECEKAN CLIENT - LAN REMOTE DESKTOP"
echo "================================================================"
echo ""

# 1. Cek Service Systemctl
echo "--- [1] STATUS SYSTEMD SERVICE (systemctl) ---"
if systemctl list-unit-files "${SERVICE_NAME}.service" >/dev/null 2>&1; then
    IS_ACTIVE=$(systemctl is-active "${SERVICE_NAME}.service" 2>/dev/null || echo "inactive")
    IS_ENABLED=$(systemctl is-enabled "${SERVICE_NAME}.service" 2>/dev/null || echo "disabled")
    
    if [ "$IS_ACTIVE" = "active" ]; then
        echo " Status Service   : [AKTIF / RUNNING 🟢]"
    else
        echo " Status Service   : [TIDAK AKTIF / STOPPED 🔴] ($IS_ACTIVE)"
    fi
    echo " Autostart Boot   : $IS_ENABLED"
    echo " Nama Service     : ${SERVICE_NAME}"
    echo " Perintah Cek     : sudo systemctl status ${SERVICE_NAME}"
    echo " Perintah Log     : sudo journalctl -u ${SERVICE_NAME} -f"
else
    echo " Service '${SERVICE_NAME}' BELUM terdaftar di systemd."
    echo " -> Untuk mendaftarkan agar jalan 24/7 otomatis: sudo ./client/install_client_service.sh"
fi
echo ""

# 2. Cek Proses client.py di Sistem
echo "--- [2] STATUS PROSES APLIKASI DI BACKGROUND ---"
CLIENT_PIDS=$(pgrep -f "python3.*client\.py" || true)

if [ -n "$CLIENT_PIDS" ]; then
    echo " Proses Client    : DITEMUKAN BERJALAN (PID: $CLIENT_PIDS) 🟢"
    ps -fp $CLIENT_PIDS -o pid,user,%cpu,%mem,etime,cmd
else
    echo " Proses Client    : TIDAK DITEMUKAN BERJALAN 🔴"
fi
echo ""

# 3. Cek Konfigurasi config.json
echo "--- [3] KONFIGURASI AKTIF (config.json) ---"
CFG_FILE="$SCRIPT_DIR/config.json"
if [ -f "$CFG_FILE" ]; then
    python3 -c "
import json
try:
    with open('$CFG_FILE') as f:
        d = json.load(f)
    print(' Target IP Server : ' + str(d.get('server_ip') or '(Auto-Discovery via UDP)'))
    print(' Target Port      : ' + str(d.get('server_port', 8001)))
    print(' Device ID        : ' + str(d.get('device_id', '')))
    print(' Auto Discovery   : ' + str(d.get('auto_discover', True)))
except Exception as e:
    print(' Gagal membaca config:', e)
" 2>/dev/null || cat "$CFG_FILE"
else
    echo " File config.json belum ada di $CFG_FILE"
fi
echo ""

# 4. Panduan Tindakan Cepat
echo "================================================================"
echo " TINDAKAN CEPAT:"
echo " 1. Buka GUI Ganti IP Server : ./client/settings.sh (atau klik di Desktop)"
echo " 2. Nyalakan Client Service  : sudo systemctl start ${SERVICE_NAME}"
echo " 3. Restart Client Service   : sudo systemctl restart ${SERVICE_NAME}"
echo " 4. Jalankan Manual Terminal : ./client/run_client.sh"
echo "================================================================"
echo ""
