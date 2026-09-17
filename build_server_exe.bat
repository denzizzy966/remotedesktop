@echo off
title Build Standalone Admin Server EXE
cd /d "%~dp0"

echo ================================================================
echo  Building Standalone LANRemoteServer.exe for Windows
echo ================================================================
echo.
python build_server.py
pause
