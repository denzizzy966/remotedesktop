@echo off
title Uninstaller LAN Remote Desktop - Client Agent (Windows)
cd /d "%~dp0"

:: Check for Administrator Privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Meminta hak akses Administrator...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process cmd -ArgumentList '/c \"\"%~f0\"\"' -Verb RunAs"
    exit /b
)

echo ================================================================
echo  UNINSTALLER LAN REMOTE DESKTOP - CLIENT AGENT
echo  Target OS: Windows 10 / Windows 11
echo ================================================================
echo.
echo Script ini akan:
echo   1. Menghentikan client agent yang sedang aktif di latar belakang
echo   2. Menghapus tugas otomatisasi di Task Scheduler (Autostart)
echo   3. Menghapus shortcut Startup dan Desktop
echo   4. Mengembalikan kebijakan sistem Windows (Lock Screen/UAC)
echo ================================================================
echo.

set /p CONFIRM="Apakah Anda yakin ingin mencopot pemasangan Client Agent? (Y/N, default Y): "
if /i "%CONFIRM%"=="" set CONFIRM=Y
if /i not "%CONFIRM%"=="Y" (
    echo [BATAL] Pencopotan dibatalkan oleh pengguna.
    pause
    exit /b 0
)

echo.
echo [1/4] Menghentikan proses Client Agent...
taskkill /f /im LANRemoteClient.exe >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq *LAN Remote Desktop Client*" >nul 2>&1
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*client.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }" >nul 2>&1
echo   - Proses client agent berhasil dihentikan.

echo.
echo [2/4] Menghapus tugas di Windows Task Scheduler...
schtasks /delete /tn "LANRemoteDesktopClient" /f >nul 2>&1
echo   - Tugas Task Scheduler 'LANRemoteDesktopClient' berhasil dihapus.

echo.
echo [3/4] Menghapus Shortcut Startup dan Desktop...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$startupLnk = [System.IO.Path]::Combine([Environment]::GetFolderPath('Startup'), 'LAN Remote Desktop Client.lnk'); if (Test-Path $startupLnk) { Remove-Item $startupLnk -Force; Write-Host '  - Shortcut Startup dihapus.' }; " ^
    "$desktopLnk = [System.IO.Path]::Combine([Environment]::GetFolderPath('Desktop'), 'LAN Remote Desktop Client.lnk'); if (Test-Path $desktopLnk) { Remove-Item $desktopLnk -Force; Write-Host '  - Shortcut Desktop Client dihapus.' }; " ^
    "$settingsLnk = [System.IO.Path]::Combine([Environment]::GetFolderPath('Desktop'), 'Pengaturan Server LAN Remote.lnk'); if (Test-Path $settingsLnk) { Remove-Item $settingsLnk -Force; Write-Host '  - Shortcut Pengaturan Server dihapus.' }; " ^
    "$commonStartup = [System.IO.Path]::Combine([Environment]::GetFolderPath('CommonStartup'), 'LAN Remote Desktop Client.lnk'); if (Test-Path $commonStartup) { Remove-Item $commonStartup -Force; Write-Host '  - Shortcut Common Startup dihapus.' }"

echo.
echo [4/4] Mengembalikan Kebijakan Sistem Windows (SAS & UAC)...
:: Reset Software SAS and PromptOnSecureDesktop to Windows defaults
reg delete "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v SoftwareSASGeneration /f >nul 2>&1
reg delete "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v PromptOnSecureDesktop /f >nul 2>&1
echo   - Kebijakan sistem Windows berhasil dipulihkan ke pengaturan standar.

echo.
echo ================================================================
echo  PEMBERSIHAN KONFIGURASI CLIENT
echo ================================================================
set /p DEL_CONFIG="Hapus file konfigurasi client (config.json)? (Y/N, default N): "
if /i "%DEL_CONFIG%"=="Y" (
    if exist "%~dp0config.json" del /f /q "%~dp0config.json" >nul 2>&1
    echo   - File config.json berhasil dihapus.
) else (
    echo   - File config.json tetap dipertahankan.
)

echo.
echo ================================================================
echo  UNINSTALL CLIENT AGENT SELESAI DENGAN SUKSES!
echo ================================================================
echo Client Agent telah dinonaktifkan dan dihapus sepenuhnya dari Windows.
echo Komputer ini tidak lagi terhubung ke Server Admin.
echo ================================================================
echo.
pause
