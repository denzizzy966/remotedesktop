@echo off
title Hentikan LAN Remote Desktop Client
cd /d "%~dp0"

echo ================================================================
echo  Menghentikan LAN Remote Desktop Client di Background...
echo ================================================================
echo.

:: 1. Hentikan proses executable mandiri
taskkill /f /im LANRemoteClient.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Proses LANRemoteClient.exe berhasil dihentikan.
)

:: 2. Hentikan proses python / pythonw yang menjalankan client.py
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*client.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue; Write-Host ('[OK] Proses client background PID ' + $_.ProcessId + ' berhasil dihentikan.') }"

echo.
echo ================================================================
echo  Client telah berhenti berjalan.
echo ================================================================
timeout /t 2 >nul
