@echo off
:: ================================================================
::  LAN Remote Desktop Client - Silent Background Launcher (Windows)
::  Menjalankan client 100% di latar belakang tanpa jendela CMD
:: ================================================================
cd /d "%~dp0"

:: 1. Jika ada file executable mandiri (LANRemoteClient.exe windowless)
if exist "%~dp0LANRemoteClient.exe" (
    start "" "%~dp0LANRemoteClient.exe" %*
    exit /b 0
)

:: 2. Cari pythonw.exe di PATH sistem (pythonw = Python Windowed tanpa console)
where pythonw >nul 2>&1
if %errorlevel% equ 0 (
    start "" pythonw "%~dp0client.py" %*
    exit /b 0
)

:: 3. Cari pythonw.exe di direktori instalasi Python
for /f "delims=" %%i in ('python -c "import sys, os; print(os.path.join(sys.prefix, 'pythonw.exe'))" 2^>nul') do (
    if exist "%%i" (
        start "" "%%i" "%~dp0client.py" %*
        exit /b 0
    )
)

:: 4. Fallback melalui VBScript runner jika tersedia
if exist "%~dp0run_client_silent.vbs" (
    start "" wscript.exe "%~dp0run_client_silent.vbs"
    exit /b 0
)

:: 5. Fallback standar
start "" /b python "%~dp0client.py" %*
exit /b 0
