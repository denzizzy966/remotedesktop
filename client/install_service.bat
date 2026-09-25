@echo off
title Installer Service LAN Remote Desktop (Silent Background & Lock Screen)
cd /d "%~dp0"

:: 1. Check for Administrator Privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Meminta izin Administrator untuk mendaftarkan Service Background...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process cmd -ArgumentList '/c \"\"%~f0\"\"' -Verb RunAs"
    exit /b
)

echo ================================================================
echo  INSTALLER LAYANAN SISTEM (SERVICE MODE) - LAN REMOTE DESKTOP
echo  Fitur: Berjalan di Background (Tanpa Jendela CMD), Lock Screen & UAC
echo ================================================================
echo.

:: 2. Target Executable (100% Windowless / Silent)
if exist "%~dp0LANRemoteClient.exe" (
    set RUN_TARGET=%~dp0LANRemoteClient.exe
    set TASK_CMD=\"%~dp0LANRemoteClient.exe\"
    echo [OK] Executable Mandiri terdeteksi: LANRemoteClient.exe (Windowless)
) else (
    set RUN_TARGET=%~dp0run_client_silent.vbs
    set TASK_CMD=wscript.exe \"%~dp0run_client_silent.vbs\"
    echo [OK] Menggunakan Silent Runner: run_client_silent.vbs (Tanpa Jendela CMD)
)
echo.

:: 3. Configure Windows Policies for Lock Screen Remote Access & SAS
echo [1/4] Mengonfigurasi Kebijakan Sistem Windows untuk Remote Access...
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v SoftwareSASGeneration /t REG_DWORD /d 3 /f >nul 2>&1
echo   - Software SAS (Ctrl+Alt+Del) diaktifkan: OK
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
echo [3/4] Mendaftarkan Service Prioritas Tinggi di Task Scheduler...
echo ================================================================
schtasks /delete /tn "LANRemoteDesktopClient" /f >nul 2>&1

:: Create task that runs with highest administrator privileges on logon without opening any console window
schtasks /create /tn "LANRemoteDesktopClient" /tr "%TASK_CMD%" /sc onlogon /rl highest /f
if %errorlevel% equ 0 (
    echo [SUCCESS] Layanan berhasil didaftarkan sebagai Service Prioritas Tertinggi!
    echo Client otomatis berjalan di latar belakang (tanpa jendela CMD) setiap PC menyala.
) else (
    echo [WARNING] Menambahkan ke folder Startup...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$WshShell = New-Object -ComObject WScript.Shell; $StartupPath = [System.IO.Path]::Combine([Environment]::GetFolderPath('Startup'), 'LAN Remote Desktop Client.lnk'); $Shortcut = $WshShell.CreateShortcut($StartupPath); $Shortcut.TargetPath = '%RUN_TARGET%'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.WindowStyle = 7; $Shortcut.Description = 'LAN Remote Desktop Client Agent'; $Shortcut.Save()"
)

:: Buat shortcut Pengaturan Server (Ganti IP GUI) di Desktop
powershell -NoProfile -ExecutionPolicy Bypass -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([System.IO.Path]::Combine([Environment]::GetFolderPath('Desktop'), 'Pengaturan Server LAN Remote.lnk')); $Shortcut.TargetPath = '%~dp0settings.bat'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.Description = 'Ganti IP & Port Server Admin LAN Remote Desktop'; $Shortcut.Save()" >nul 2>&1
echo [OK] Shortcut Desktop 'Pengaturan Server LAN Remote' telah dibuat!
echo.

:: 6. Start Client Immediately in Background
echo ================================================================
echo [4/4] Menjalankan Client Agent di Latar Belakang...
echo ================================================================
schtasks /run /tn "LANRemoteDesktopClient" >nul 2>&1
if %errorlevel% neq 0 (
    if exist "%~dp0LANRemoteClient.exe" (
        start "" "%~dp0LANRemoteClient.exe"
    ) else (
        start "" wscript.exe "%~dp0run_client_silent.vbs"
    )
)
echo Client Agent telah aktif di latar belakang (100%% tanpa jendela CMD)!
echo Ikon monitor status tersedia di System Tray taskbar (dekat jam).
echo.
echo ================================================================
echo  INSTALASI SELESAI!
echo  Client sekarang berjalan otomatis di latar belakang dengan:
echo   - Akses Penuh Lock Screen / Layar Kunci Windows
echo   - Nol Jendela CMD / Terminal (Tidak mengganggu pengguna)
echo   - Ganti IP kapan saja via shortcut 'Pengaturan Server' di Desktop
echo   - Pengecekan status: jalankan 'status_client.bat'
echo   - Penghentian client: jalankan 'stop_client.bat'
echo ================================================================
echo.
pause
