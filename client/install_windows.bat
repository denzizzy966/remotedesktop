@echo off
title Installer LAN Remote Desktop - Client Agent (Windows 10/11)
cd /d "%~dp0"

echo ================================================================
echo  INSTALLER LAN REMOTE DESKTOP - CLIENT AGENT
echo  Target OS: Windows 10 / Windows 11
echo ================================================================
echo.

:: 1. Check if Standalone EXE exists
if exist "%~dp0LANRemoteClient.exe" (
    echo [INFO] Versi Executable Mandiri (LANRemoteClient.exe) TERSEDIA!
    echo PC ini TIDAK MEMERLUKAN Python, pip, maupun koneksi internet.
    echo Anda dapat langsung menjalankan client tanpa instalasi apapun!
    echo.
    set RUN_TARGET=%~dp0LANRemoteClient.exe
    set TASK_CMD=\"%~dp0LANRemoteClient.exe\"
    goto config_server
)

:: 2. Check Python if EXE not present
echo [1/5] Memeriksa Python di sistem...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Python tidak ditemukan di PATH dan LANRemoteClient.exe tidak ditemukan!
    echo Silakan install Python 3.9+ dari https://www.python.org/downloads/
    echo Atau gunakan file LANRemoteClient.exe yang sudah dibundel.
    echo.
    pause
    exit /b 1
)

python -c "import sys; print('Python terdeteksi:', sys.version.split()[0])"
echo.

:: 3. Upgrade pip & install dependencies (Online or Offline)
echo [2/5] Memasang pustaka client...

if exist "%~dp0offline_packages" (
    echo [OFFLINE MODE] Folder 'offline_packages' terdeteksi!
    echo Memasang dependensi dari cache lokal (tanpa butuh internet)...
    python -m pip install --no-index --find-links="%~dp0offline_packages" -r "%~dp0requirements.txt"
) else if exist "%~dp0requirements.txt" (
    echo Memasang pustaka dari requirements.txt...
    python -m pip install -r "%~dp0requirements.txt"
) else (
    echo Mengunduh pustaka client secara langsung...
    python -m pip install websockets psutil mss pillow pynput pyautogui pyperclip requests
)

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Gagal memasang pustaka.
    echo Jika PC ini offline, gunakan file LANRemoteClient.exe atau folder offline_packages.
    pause
    exit /b 1
)
echo Pustaka client berhasil dipasang!
echo.
if exist "%~dp0LANRemoteClient.exe" (
    set RUN_TARGET=%~dp0LANRemoteClient.exe
    set TASK_CMD=\"%~dp0LANRemoteClient.exe\"
) else (
    set RUN_TARGET=%~dp0run_client_silent.vbs
    set TASK_CMD=wscript.exe \"%~dp0run_client_silent.vbs\"
)

:config_server
:: 4. Server IP and Port Configuration
echo ================================================================
echo [3/5] Konfigurasi Koneksi Server Admin
echo ================================================================
echo Secara bawaan, client akan otomatis mencari IP dan Port Server di LAN via UDP.
echo Jika jaringan switch Anda memblokir UDP broadcast atau Anda ingin
echo menentukan IP dan Port server secara spesifik, silakan isi di bawah ini.
echo (Tekan ENTER langsung untuk menggunakan Auto-Discovery otomatis)
echo.
set /p TARGET_IP="Masukkan IP Server Admin (kosongkan untuk Auto-Discovery): "
if not "%TARGET_IP%"=="" (
    set /p TARGET_PORT="Masukkan Port Server Admin (default: 8001): "
    if "%TARGET_PORT%"=="" set TARGET_PORT=8001
    
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$cfg = @{ server_url = ''; server_ip = '%TARGET_IP%'; server_port = [int]'%TARGET_PORT%'; device_id = ''; auto_discover = $false } | ConvertTo-Json; Set-Content -Path '%~dp0config.json' -Value $cfg"
    echo Konfigurasi tersimpan: Server IP = %TARGET_IP%, Port = %TARGET_PORT%
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$cfg = @{ server_url = ''; server_ip = ''; server_port = 8001; device_id = ''; auto_discover = $true } | ConvertTo-Json; Set-Content -Path '%~dp0config.json' -Value $cfg"
    echo Mode Auto-Discovery aktif: Client akan mencari IP dan Port server secara otomatis.
)
echo.

:: 5. Create Windows Startup Autostart (Optional)
echo ================================================================
echo [4/5] Konfigurasi Autostart saat Windows menyala...
echo ================================================================
echo Apakah Anda ingin client ini otomatis berjalan di latar belakang
echo (tanpa jendela CMD) setiap kali komputer dihidupkan / restart?
set /p AUTOSTART="Jalankan otomatis saat Windows startup? (Y/N, default Y): "
if /i "%AUTOSTART%"=="" set AUTOSTART=Y
if /i "%AUTOSTART%"=="Y" (
    :: Try registering high-privilege Task Scheduler task (enables lock screen access & windowless)
    schtasks /create /tn "LANRemoteDesktopClient" /tr "%TASK_CMD%" /sc onlogon /rl highest /f >nul 2>&1
    if %errorlevel% == 0 (
        echo [OK] Berhasil didaftarkan ke Task Scheduler (Bypass UAC & Akses Lock Screen)!
    )
    if exist "%~dp0LANRemoteClient.exe" (
        powershell -NoProfile -ExecutionPolicy Bypass -Command "$WshShell = New-Object -ComObject WScript.Shell; $StartupPath = [System.IO.Path]::Combine([Environment]::GetFolderPath('Startup'), 'LAN Remote Desktop Client.lnk'); $Shortcut = $WshShell.CreateShortcut($StartupPath); $Shortcut.TargetPath = '%~dp0LANRemoteClient.exe'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.WindowStyle = 7; $Shortcut.Description = 'LAN Remote Desktop Client Agent'; $Shortcut.Save()"
    ) else (
        powershell -NoProfile -ExecutionPolicy Bypass -Command "$WshShell = New-Object -ComObject WScript.Shell; $StartupPath = [System.IO.Path]::Combine([Environment]::GetFolderPath('Startup'), 'LAN Remote Desktop Client.lnk'); $Shortcut = $WshShell.CreateShortcut($StartupPath); $Shortcut.TargetPath = 'wscript.exe'; $Shortcut.Arguments = '\"%~dp0run_client_silent.vbs\"'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.WindowStyle = 7; $Shortcut.Description = 'LAN Remote Desktop Client Agent'; $Shortcut.Save()"
    )
    echo Shortcut berhasil ditambahkan ke folder Windows Startup!
)
echo.

:: 6. Create Desktop Shortcut (Optional)
echo ================================================================
echo [5/5] Membuat Shortcut Desktop...
echo ================================================================
set /p CREATE_SHORTCUT="Buat shortcut di Desktop untuk Client & Pengaturan? (Y/N, default Y): "
if /i "%CREATE_SHORTCUT%"=="" set CREATE_SHORTCUT=Y
if /i "%CREATE_SHORTCUT%"=="Y" (
    if exist "%~dp0LANRemoteClient.exe" (
        powershell -NoProfile -ExecutionPolicy Bypass -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([System.IO.Path]::Combine([Environment]::GetFolderPath('Desktop'), 'LAN Remote Desktop Client.lnk')); $Shortcut.TargetPath = '%~dp0LANRemoteClient.exe'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.Description = 'LAN Remote Desktop Client Agent'; $Shortcut.Save()"
    ) else (
        powershell -NoProfile -ExecutionPolicy Bypass -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([System.IO.Path]::Combine([Environment]::GetFolderPath('Desktop'), 'LAN Remote Desktop Client.lnk')); $Shortcut.TargetPath = 'wscript.exe'; $Shortcut.Arguments = '\"%~dp0run_client_silent.vbs\"'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.Description = 'LAN Remote Desktop Client Agent'; $Shortcut.Save()"
    )
    echo Shortcut Desktop 'LAN Remote Desktop Client' berhasil dibuat!
    
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([System.IO.Path]::Combine([Environment]::GetFolderPath('Desktop'), 'Pengaturan Server LAN Remote.lnk')); $Shortcut.TargetPath = '%~dp0settings.bat'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.Description = 'Ganti IP & Port Server Admin LAN Remote Desktop'; $Shortcut.Save()"
    echo Shortcut Desktop 'Pengaturan Server LAN Remote' berhasil dibuat!
)

echo.
echo ================================================================
echo  INSTALASI CLIENT AGENT SELESAI!
echo ================================================================
echo Client berjalan di latar belakang (100%% tanpa jendela CMD/terminal):
echo   - Menjalankan client  : Klik ganda 'run_client.bat' atau shortcut Desktop
echo   - Ganti IP Server GUI : Klik ganda shortcut 'Pengaturan Server LAN Remote'
echo   - Cek Status Berjalan : Jalankan 'status_client.bat'
echo   - Hentikan Client     : Jalankan 'stop_client.bat'
echo ================================================================
echo.
pause
