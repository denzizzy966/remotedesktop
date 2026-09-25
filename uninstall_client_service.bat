@echo off
cd /d "%~dp0"
call "%~dp0client\uninstall_service.bat" %*
