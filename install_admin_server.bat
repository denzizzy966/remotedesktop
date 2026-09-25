@echo off
title Installer LAN Remote Desktop - Admin Server (Windows 10/11)
cd /d "%~dp0"

echo ================================================================
echo  INSTALLER LAN REMOTE DESKTOP - ADMIN SERVER
echo  Target OS: Windows 10 / Windows 11
echo ================================================================
echo.

:: 1. Check Python
echo [1/4] Memeriksa instalasi Python di sistem...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Python tidak ditemukan di PATH!
    echo Silakan install Python 3.9+ dari: https://www.python.org/downloads/
    echo PENTING: Saat instalasi Python, WAJIB centang "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

python -c "import sys; print('Python terdeteksi:', sys.version.split()[0])"
echo.

:: 2. Install pip dependencies (Online or Offline)
echo [2/4] Memasang dependensi server (FastAPI, WebSockets, psutil)...
if exist "%~dp0server\offline_packages" (
    echo [OFFLINE MODE] Folder 'server\offline_packages' terdeteksi!
    echo Memasang pustaka server dari paket offline lokal (tanpa perlu koneksi internet)...
    python -m pip install --no-index --find-links="%~dp0server\offline_packages" fastapi uvicorn websockets psutil
) else (
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
)
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Gagal memasang dependensi server.
    pause
    exit /b 1
)
echo Dependensi server berhasil dipasang!
echo.

:: 3. Initial Admin Password Setup
echo [3/4] Konfigurasi Password Admin...
echo Anda dapat mengatur password admin sekarang dari console,
echo atau Anda juga dapat mengaturnya nanti saat pertama kali membuka web dashboard.
echo.
set /p SETUP_PASS="Ingin atur password admin sekarang? (Y/N, default Y): "
if /i "%SETUP_PASS%"=="" set SETUP_PASS=Y
if /i "%SETUP_PASS%"=="Y" (
    echo.
    python reset_password.py
) else (
    echo Password admin dapat diatur saat pertama kali membuka dashboard di browser.
)
echo.

:: 4. Create Desktop Shortcut (Optional)
echo [4/4] Membuat Shortcut Desktop untuk Admin Server...
set /p CREATE_SHORTCUT="Buat shortcut di Desktop untuk menjalankan Admin Server? (Y/N, default Y): "
if /i "%CREATE_SHORTCUT%"=="" set CREATE_SHORTCUT=Y
if /i "%CREATE_SHORTCUT%"=="Y" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([System.IO.Path]::Combine([Environment]::GetFolderPath('Desktop'), 'LAN Remote Desktop Server.lnk')); $Shortcut.TargetPath = '%~dp0run_server.bat'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.Description = 'LAN Remote Desktop Server & Admin Dashboard'; $Shortcut.Save()"
    echo Shortcut Desktop 'LAN Remote Desktop Server' berhasil dibuat!
)

echo.
echo ================================================================
echo  INSTALASI ADMIN SERVER SELESAI!
echo ================================================================
echo Untuk menjalankan server sekarang, klik:
echo   - run_server.bat
echo   - Atau shortcut 'LAN Remote Desktop Server' di Desktop Anda
echo.
echo Dashboard Web dapat dibuka di:
echo   - http://localhost:8001 (atau port bebas yang aktif)
echo   - Jika lupa password di kemudian hari, jalankan: reset_password.bat
echo ================================================================
echo.
pause
