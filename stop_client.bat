@echo off
cd /d "%~dp0"
call "%~dp0client\stop_client.bat" %*
