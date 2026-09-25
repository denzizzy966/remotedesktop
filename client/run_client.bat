@echo off
title LAN Remote Desktop Client
cd /d "%~dp0"
echo ========================================================
echo  LAN Remote Desktop Client Agent
echo ========================================================

if exist "%~dp0LANRemoteClient.exe" (
    echo Menjalankan versi executable mandiri (LANRemoteClient.exe)...
    "%~dp0LANRemoteClient.exe" %*
    goto finish
)

python client.py %*
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Client terhenti atau terjadi kesalahan.
    echo Pastikan Python sudah terpasang atau gunakan file LANRemoteClient.exe
    pause
)

:finish
