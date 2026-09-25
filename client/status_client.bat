@echo off
title Status LAN Remote Desktop Client
cd /d "%~dp0"

echo ================================================================
echo       STATUS PENGECEKAN CLIENT WINDOWS (BACKGROUND)
echo ================================================================
echo.

:: 1. Cek Proses Aktif di Task Manager
echo [1] STATUS PROSES BACKGROUND:
set CLIENT_RUNNING=0

tasklist /fi "imagename eq LANRemoteClient.exe" | findstr /i "LANRemoteClient.exe" >nul 2>&1
if %errorlevel% equ 0 (
    echo   [AKTIF 🟢] LANRemoteClient.exe terdeteksi berjalan di background!
    tasklist /fi "imagename eq LANRemoteClient.exe"
    set CLIENT_RUNNING=1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "$procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*client.py*' }; if ($procs) { foreach ($p in $procs) { Write-Host ('  [AKTIF 🟢] Python Client PID: ' + $p.ProcessId + ' | ' + $p.Name); }; exit 0 } else { exit 1 }"
if %errorlevel% equ 0 (
    set CLIENT_RUNNING=1
)

if %CLIENT_RUNNING% equ 0 (
    echo   [TIDAK AKTIF 🔴] Client saat ini TIDAK sedang berjalan.
)
echo.

:: 2. Cek Layanan di Task Scheduler (Windows Service Mode)
echo [2] STATUS SERVICE TASK SCHEDULER:
schtasks /query /tn "LANRemoteDesktopClient" >nul 2>&1
if %errorlevel% equ 0 (
    echo   [TERPASANG 🟢] Task Scheduler 'LANRemoteDesktopClient' aktif (Akses Lock Screen).
    schtasks /query /tn "LANRemoteDesktopClient" /fo list | findstr /i "Status TaskName Next Last"
) else (
    echo   [INFO] Belum didaftarkan ke Task Scheduler.
    echo   (Untuk mengaktifkan akses Lock Screen 24/7, jalankan: install_service.bat)
)
echo.

:: 3. Konfigurasi Aktif
echo [3] TARGET SERVER (config.json):
if exist "%~dp0config.json" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$cfg = Get-Content -Raw '%~dp0config.json' | ConvertFrom-Json; Write-Host ('  Server Target : ' + ($cfg.server_ip ? ($cfg.server_ip + ':' + $cfg.server_port) : 'Auto-Discovery via UDP')); Write-Host ('  Device ID     : ' + $cfg.device_id)"
) else (
    echo   File config.json belum dibuat.
)
echo.

echo ================================================================
echo TINDAKAN:
echo  - Jalankan Client (Silent) : Klik ganda 'run_client.bat'
echo  - Ganti IP Server (GUI)    : Klik ganda 'settings.bat'
echo  - Hentikan Client          : Klik ganda 'stop_client.bat'
echo ================================================================
echo.
pause
