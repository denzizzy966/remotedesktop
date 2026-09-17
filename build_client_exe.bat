@echo off
title Build Standalone Client EXE (LAN Remote Desktop)
cd /d "%~dp0"

echo ================================================================
echo  Building Standalone LANRemoteClient.exe for Windows
echo ================================================================
echo.
python build_client.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build gagal. Pastikan PyInstaller terpasang (pip install pyinstaller).
    pause
    exit /b 1
)

:: Copy resulting exe directly into client folder for easy distribution
if exist "dist\LANRemoteClient.exe" (
    copy /y "dist\LANRemoteClient.exe" "client\LANRemoteClient.exe" >nul
    echo.
    echo File 'LANRemoteClient.exe' telah disalin juga ke folder 'client\'.
    echo Sekarang Anda cukup meng-copy folder 'client\' atau file 'client\LANRemoteClient.exe'
    echo ke PC klien manapun tanpa perlu internet atau Python!
)

echo.
pause
