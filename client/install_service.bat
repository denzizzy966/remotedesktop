@echo off
title Installer Service LAN Remote Desktop (Dukungan Lock Screen & UAC)
cd /d "%~dp0"

:: 1. Check for Administrator Privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Meminta izin Administrator untuk mengaktifkan akses Lock Screen...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process cmd -ArgumentList '/c \"\"%~f0\"\"' -Verb RunAs"
    exit /b
)

echo ================================================================
echo  INSTALLER LAYANAN SISTEM (SERVICE MODE) - LAN REMOTE DESKTOP
echo  Fitur: Akses Penuh Lock Screen, Windows Login, dan Prompt UAC
echo ================================================================
echo.

:: 2. Target Executable
if exist "%~dp0LANRemoteClient.exe" (
    set RUN_TARGET=%~dp0LANRemoteClient.exe
    echo [OK] Executable Mandiri terdeteksi: LANRemoteClient.exe
) else (
    set RUN_TARGET=%~dp0run_client.bat
    echo [INFO] Menggunakan launcher batch: run_client.bat
)
echo.

:: 3. Configure Windows Policies for Lock Screen Remote Access & SAS
echo [1/4] Mengonfigurasi Kebijakan Sistem Windows untuk Remote Access...
:: Enable Software SAS (Ctrl+Alt+Del injection)
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v SoftwareSASGeneration /t REG_DWORD /d 3 /f >nul 2>&1
echo   - Software SAS (Ctrl+Alt+Del) diaktifkan: OK

:: Configure UAC desktop prompt compatibility
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v PromptOnSecureDesktop /t REG_DWORD /d 0 /f >nul 2>&1
echo   - Kompatibilitas prompt UAC diaktifkan: OK
echo.

:: 4. Server Configuration
echo ================================================================
echo [2/4] Konfigurasi Koneksi Server Admin
echo ================================================================
if exist "%~dp0config.json" (
    echo Konfigurasi 'config.json' sudah ada.
    set /p RECONFIG="Apakah ingin mengubah IP/Port Server? (Y/N, default N): "
    if /i "%RECONFIG%"=="Y" goto prompt_ip
    goto register_task
)

:prompt_ip
set /p TARGET_IP="Masukkan IP Server Admin (kosongkan untuk Auto-Discovery): "
if not "%TARGET_IP%"=="" (
    set /p TARGET_PORT="Masukkan Port Server Admin (default: 8001): "
    if "%TARGET_PORT%"=="" set TARGET_PORT=8001
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$cfg = @{ server_url = ''; server_ip = '%TARGET_IP%'; server_port = [int]'%TARGET_PORT%'; device_id = ''; auto_discover = $false } | ConvertTo-Json; Set-Content -Path '%~dp0config.json' -Value $cfg"
    echo Konfigurasi tersimpan: Server IP = %TARGET_IP%, Port = %TARGET_PORT%
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$cfg = @{ server_url = ''; server_ip = ''; server_port = 8001; device_id = ''; auto_discover = $true } | ConvertTo-Json; Set-Content -Path '%~dp0config.json' -Value $cfg"
    echo Mode Auto-Discovery aktif.
)
echo.

:register_task
:: 5. Register in Windows Task Scheduler with Highest Privileges
echo ================================================================
echo [3/4] Mendaftarkan Layanan Prioritas Tinggi di Task Scheduler...
echo ================================================================
schtasks /delete /tn "LANRemoteDesktopClient" /f >nul 2>&1

:: Create task that runs with highest administrator privileges on logon
schtasks /create /tn "LANRemoteDesktopClient" /tr "\"%RUN_TARGET%\"" /sc onlogon /rl highest /f
if %errorlevel% equ 0 (
    echo [SUCCESS] Layanan berhasil didaftarkan dengan hak akses Prioritas Tertinggi (Highest Privilege)!
    echo Client akan otomatis berjalan dengan akses Lock Screen setiap kali PC menyala.
) else (
    echo [WARNING] Gagal mendaftarkan ke Task Scheduler. Menambahkan ke folder Startup biasa...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$WshShell = New-Object -ComObject WScript.Shell; $StartupPath = [System.IO.Path]::Combine([Environment]::GetFolderPath('Startup'), 'LAN Remote Desktop Client.lnk'); $Shortcut = $WshShell.CreateShortcut($StartupPath); $Shortcut.TargetPath = '%RUN_TARGET%'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.WindowStyle = 7; $Shortcut.Description = 'LAN Remote Desktop Client Agent'; $Shortcut.Save()"
)
echo.

:: 6. Start Client Immediately
echo ================================================================
echo [4/4] Menjalankan Client Agent Sekarang...
echo ================================================================
schtasks /run /tn "LANRemoteDesktopClient" >nul 2>&1
if %errorlevel% neq 0 (
    start "" "%RUN_TARGET%"
)
echo Client Agent telah aktif di latar belakang!
echo.
echo ================================================================
echo  INSTALASI SELESAI!
echo  Client sekarang memiliki hak akses penuh untuk:
echo   - Menampilkan Lock Screen / Layar Kunci Windows
echo   - Mengisi password / PIN dari Dashboard Admin
echo   - Menerima sinyal Wake Screen dan Ctrl+Alt+Del
echo ================================================================
echo.
pause
