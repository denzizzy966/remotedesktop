@echo off
title Download Offline PIP Packages for Server
cd /d "%~dp0"

echo ================================================================
echo  Downloading Server PIP Packages for Offline Installation...
echo ================================================================
echo.
echo Mengunduh seluruh paket wheel (.whl) untuk Server (Windows & Linux).
echo Paket akan disimpan di folder: %~dp0offline_packages
echo.

if not exist "%~dp0offline_packages" mkdir "%~dp0offline_packages"

:: 1. Download universal and Windows wheels
echo [1/2] Mengunduh paket Windows & Universal...
python -m pip download fastapi uvicorn websockets psutil -d "%~dp0offline_packages"

:: 2. Download Linux x86_64 wheels for Python 3.10
echo [2/2] Mengunduh paket Linux x86_64 (Ubuntu 22.04 / Python 3.10)...
python -m pip download --platform manylinux2014_x86_64 --implementation cp --python-version 310 --only-binary=:all: fastapi uvicorn websockets psutil -d "%~dp0offline_packages"

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
echo ================================================================
echo.
pause
