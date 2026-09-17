@echo off
title Download Offline PIP Packages for Client
cd /d "%~dp0"

echo ================================================================
echo  Downloading PIP Packages for Offline Installation...
echo ================================================================
echo.
echo Memerlukan koneksi internet di PC ini untuk mengunduh file wheel (.whl).
echo Paket akan disimpan di folder: %~dp0offline_packages
echo.

if not exist "%~dp0offline_packages" mkdir "%~dp0offline_packages"

python -m pip download -r "%~dp0requirements.txt" -d "%~dp0offline_packages"

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Gagal mengunduh paket. Pastikan koneksi internet aktif.
    pause
    exit /b 1
)

echo.
echo ================================================================
echo [SUCCESS] Seluruh file .whl berhasil diunduh ke folder:
echo %~dp0offline_packages
echo.
echo Sekarang Anda bisa menyalin folder 'client' ini ke PC offline mana saja!
echo Di PC offline, cukup jalankan 'install_windows.bat' tanpa butuh internet.
echo ================================================================
echo.
pause
