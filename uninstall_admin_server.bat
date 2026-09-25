@echo off
title Uninstaller LAN Remote Desktop - Admin Server (Windows)
cd /d "%~dp0"

:: Check for Administrator Privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Meminta hak akses Administrator...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process cmd -ArgumentList '/c \"\"%~f0\"\"' -Verb RunAs"
    exit /b
)

echo ================================================================
echo  UNINSTALLER LAN REMOTE DESKTOP - ADMIN SERVER
echo  Target OS: Windows 10 / Windows 11
echo ================================================================
echo.
echo Script ini akan:
echo   1. Menghentikan proses server yang sedang berjalan
echo   2. Menghapus shortcut Desktop dan Startup server
echo   3. Menghapus tugas otomatisasi di Task Scheduler (jika ada)
echo   4. Menghapus aturan Firewall server di Windows Defender Firewall
echo ================================================================
echo.

set /p CONFIRM="Apakah Anda yakin ingin mencopot pemasangan Admin Server? (Y/N, default Y): "
if /i "%CONFIRM%"=="" set CONFIRM=Y
if /i not "%CONFIRM%"=="Y" (
    echo [BATAL] Pencopotan dibatalkan oleh pengguna.
    pause
    exit /b 0
)

echo.
echo [1/4] Menghentikan proses server yang sedang aktif...
:: Stop Python server running run_server.py / uvicorn / main.py
taskkill /f /fi "WINDOWTITLE eq LAN Remote Desktop Server*" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq *run_server.py*" >nul 2>&1
wmic process where "commandline like '%%run_server.py%%'" call terminate >nul 2>&1
wmic process where "commandline like '%%server.main:app%%'" call terminate >nul 2>&1
echo   - Proses server berhasil dihentikan.

echo.
echo [2/4] Menghapus Shortcut Desktop dan Startup...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$desktopLnk = [System.IO.Path]::Combine([Environment]::GetFolderPath('Desktop'), 'LAN Remote Desktop Server.lnk'); if (Test-Path $desktopLnk) { Remove-Item $desktopLnk -Force; Write-Host '  - Shortcut Desktop dihapus.' }; " ^
    "$startupLnk = [System.IO.Path]::Combine([Environment]::GetFolderPath('Startup'), 'LAN Remote Desktop Server.lnk'); if (Test-Path $startupLnk) { Remove-Item $startupLnk -Force; Write-Host '  - Shortcut Startup dihapus.' }"

echo.
echo [3/4] Menghapus tugas di Task Scheduler (jika ada)...
schtasks /delete /tn "LANRemoteDesktopServer" /f >nul 2>&1
schtasks /delete /tn "LANRemoteServer" /f >nul 2>&1
echo   - Pemeriksaan Task Scheduler selesai.

echo.
echo [4/4] Menghapus aturan Windows Firewall...
netsh advfirewall firewall delete rule name="LAN Remote Desktop Web Admin" >nul 2>&1
netsh advfirewall firewall delete rule name="LAN Remote Desktop Server" >nul 2>&1
netsh advfirewall firewall delete rule name="LAN Remote Desktop Discovery" >nul 2>&1
echo   - Aturan firewall berhasil dibersihkan.

echo.
echo ================================================================
echo  PEMBERSIHAN DATA DAN KONFIGURASI
echo ================================================================
echo File data server meliputi password admin (config.json) dan
echo daftar nama/alias komputer (device_notes.json).
set /p DEL_DATA="Hapus file konfigurasi & database catatan perangkat? (Y/N, default N): "
if /i "%DEL_DATA%"=="Y" (
    if exist "%~dp0server\config.json" del /f /q "%~dp0server\config.json" >nul 2>&1
    if exist "%~dp0server\device_notes.json" del /f /q "%~dp0server\device_notes.json" >nul 2>&1
    echo   - File konfigurasi dan catatan perangkat berhasil dihapus.
) else (
    echo   - File konfigurasi dan catatan perangkat tetap dipertahankan.
)

echo.
echo ================================================================
echo  UNINSTALL ADMIN SERVER SELESAI DENGAN SUKSES!
echo ================================================================
echo Layanan Admin Server telah dinonaktifkan sepenuhnya dari sistem.
echo Folder project ini sekarang aman untuk dihapus jika tidak lagi digunakan.
echo ================================================================
echo.
pause
