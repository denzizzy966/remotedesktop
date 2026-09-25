@echo off
title Download Offline PIP Packages for Server (Windows & Linux)
cd /d "%~dp0"

echo ================================================================
echo  Downloading Server PIP Packages for Offline Installation...
echo ================================================================
echo.
echo Mengunduh seluruh paket wheel (.whl) untuk Server (Windows & Linux).
echo Paket akan disimpan di folder: %~dp0offline_packages
echo.

if not exist "%~dp0offline_packages" mkdir "%~dp0offline_packages"

:: 1. Download universal and Windows wheels (Python 3.10)
echo [1/4] Mengunduh paket Windows & Universal (Python 3.10)...
python -m pip download fastapi uvicorn websockets psutil -d "%~dp0offline_packages"

:: 2. Download Windows wheels for Python 3.12
echo [2/4] Mengunduh paket Windows x86_64 (Python 3.12)...
python -m pip download --platform win_amd64 --implementation cp --python-version 312 --only-binary=:all: pydantic_core websockets -d "%~dp0offline_packages"

:: 3. Download Linux x86_64 wheels for Python 3.10 (Ubuntu 22.04 LTS)
echo [3/4] Mengunduh paket Linux x86_64 (Ubuntu 22.04 / Python 3.10)...
python -m pip download --platform manylinux2014_x86_64 --implementation cp --python-version 310 --only-binary=:all: fastapi uvicorn websockets psutil -d "%~dp0offline_packages"

:: 4. Download Linux x86_64 wheels for Python 3.12 (Linux Mint 22 / Ubuntu 24.04)
echo [4/4] Mengunduh paket Linux x86_64 (Linux Mint 22 / Python 3.12)...
python -m pip download --platform manylinux2014_x86_64 --implementation cp --python-version 312 --only-binary=:all: pydantic_core websockets -d "%~dp0offline_packages"

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Terjadi kesalahan saat mengunduh beberapa paket.
    pause
    exit /b 1
)

echo.
echo ================================================================
echo [SUCCESS] Seluruh file .whl server berhasil diunduh ke folder:
echo %~dp0offline_packages
echo.
echo Sekarang Anda bisa menyalin folder server ini ke PC offline mana saja!
echo - Di Windows : Jalankan 'install_admin_server.bat' (tanpa butuh internet).
echo - Di Linux   : Jalankan 'sudo ./install_admin_server.sh' (tanpa butuh internet).
echo ================================================================
echo.
pause
