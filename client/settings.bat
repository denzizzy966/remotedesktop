@echo off
title LAN Remote Client - Pengaturan Server
cd /d "%~dp0"

if exist "%~dp0LANRemoteClient.exe" (
    "%~dp0LANRemoteClient.exe" --settings
    goto finish
)

python client.py --settings
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Gagal membuka antarmuka pengaturan.
    pause
)

:finish
