@echo off
title Uninstaller Service LAN Remote Desktop
cd /d "%~dp0"

net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process cmd -ArgumentList '/c \"\"%~f0\"\"' -Verb RunAs"
    exit /b
)

echo Menghapus layanan LAN Remote Desktop dari sistem...
schtasks /delete /tn "LANRemoteDesktopClient" /f >nul 2>&1
taskkill /f /im LANRemoteClient.exe >nul 2>&1
taskkill /f /im python.exe /fi "WINDOWTITLE eq *client.py*" >nul 2>&1

powershell -NoProfile -ExecutionPolicy Bypass -Command "$StartupPath = [System.IO.Path]::Combine([Environment]::GetFolderPath('Startup'), 'LAN Remote Desktop Client.lnk'); if (Test-Path $StartupPath) { Remove-Item $StartupPath -Force }"

echo [OK] Layanan berhasil dihapus dari sistem.
pause
