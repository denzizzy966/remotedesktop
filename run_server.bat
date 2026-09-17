@echo off
title LAN Remote Desktop Server
echo Starting LAN Remote Desktop Server...
cd /d "%~dp0"
python run_server.py
pause
