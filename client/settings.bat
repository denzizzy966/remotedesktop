@echo off
title LAN Remote Client - Pengaturan Server
cd /d "%~dp0"

if exist "%~dp0LANRemoteClient.exe" (
    start "" "%~dp0LANRemoteClient.exe" --settings
    exit /b 0
)

where pythonw >nul 2>&1
if %errorlevel% equ 0 (
    start "" pythonw "%~dp0client.py" --settings
    exit /b 0
)

start "" python "%~dp0client.py" --settings
exit /b 0
