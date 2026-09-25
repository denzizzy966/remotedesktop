# 🖥️ LAN Remote Desktop & Centralized Admin Dashboard

A lightweight, high-performance, cross-platform remote desktop and fleet monitoring system designed specifically for **Local Area Networks (LAN)**.

Support Platform:
- **Windows 10 / 11**
- **Linux Mint 22 / Ubuntu 22.04 LTS** (X11 / Xorg)
- **Admin Dashboard**: Accessible from any web browser on the local network (`http://<SERVER_IP>:8000`).

---

## ✨ Fitur Utama (Key Features)

### 1. 📊 Centralized Admin Dashboard
* **Client Auto-Discovery**: Client dapat menemukan IP Server secara otomatis menggunakan UDP broadcast beacon pada LAN (port 8002), tanpa perlu konfigurasi IP manual.
* **Informasi Client & Status PC**:
  * Hostname, Username yang sedang login, dan Alamat IP LAN.
  * Status real-time: **Online (🟢)**, **In Remote Session (🔵)**, **Offline (⚪)**.
  * Tipe & Versi OS (Windows 11, Windows 10, Ubuntu 22.04, Linux Mint 22).
  * System Uptime.
* **Monitor Resource & Usage PC Real-time**:
  * **CPU Usage %** (dengan bar animasi dan indikator core).
  * **RAM Usage %** (digunakan / kapasitas total dalam GB).
  * **Storage / Disk Usage %** (kapasitas terpakai / total).
  * **Live Desktop Thumbnail**: Preview layar client yang diperbarui otomatis setiap beberapa detik.
* **Filter & Pencarian**:
  * Cari client berdasarkan Hostname, IP, atau Username.
  * Filter berdasarkan OS (Windows / Linux) atau Status (Online / In Session / Offline).

### 2. 🎮 Interactive Remote Desktop Control
* **Ultra-Low Latency Screen Streaming**: Frame stream adaptif berbasis WebSocket menggunakan kompresi JPEG dinamis (20-30 FPS).
* **Kontrol Mouse Lengkap**:
  * Gerakan kursor dengan koordinat yang dinormalisasi (presisi terlepas dari resolusi layar browser/layar target).
  * Klik kiri, klik kanan (browser context menu dinonaktifkan khusus pada canvas), klik tengah, double-click, drag & drop, dan mouse wheel scroll.
* **Kontrol Keyboard Penuh**:
  * Meneruskan tombol keyboard langsung ke PC client tanpa terhalang shortcut browser bawaan (seperti F5, Tab, Ctrl+W, dll.).
  * **Hotkey Toolbar**: Tombol cepat untuk `[Win]`, `[Win+D]`, `[Alt+Tab]`, `[Ctrl+Shift+Esc]`, `[Ctrl+C]`, `[Ctrl+V]`.
  * Fitur **"Type Text / Paste"** untuk mengetikkan teks panjang langsung ke client.
* **Multi-Monitor Support**: Pilihan monitor jika client memiliki lebih dari 1 layar.
* **Profil Kualitas**:
  * *Performance (480p / Low Latency)*: Sangat cepat dan responsif.
  * *Balanced (720p)*: Rekomendasi standar LAN.
  * *High Quality (1080p)*: Tampilan tajam dan jernih.
* **Mode Kontrol**: Toggle antara *Full Control* dan *View-Only*.
* **Fullscreen Mode**: Pengalaman remote desktop layar penuh.

### 3. 🔐 Keamanan, Login & Settings Admin
* **Sistem Autentikasi Password**: Dashboard admin dilindungi password aman (PBKDF2-HMAC-SHA256 + 100.000 iterasi).
* **Fitur Login**:
  * Opsi **Show Password** (ikon mata untuk menampilkan/menyembunyikan teks password).
  * Opsi **Remember Me** (menyimpan sesi login aman selama 30 hari).
* **First-Time Setup Wizard**: Saat server pertama kali dipasang, sistem akan menampilkan panduan pembuatan password admin awal (bisa diatur via web atau terminal).
* **Reset Password dari Console**: Jika lupa password, admin dapat langsung mereset password melalui terminal console dengan menjalankan `reset_password.bat` atau `python reset_password.py`.
* **Modal Settings di Admin**: Menu pengaturan di dashboard admin untuk:
  * Mengubah password admin secara langsung.
  * Mengatur nama server, batas waktu sesi (session timeout), dan durasi Remember Me.
  * Meninjau port aktif web dan port UDP discovery.

### 4. 🛠️ Remote Administrator Tools Tambahan
* **Remote Terminal / Shell**: Jalankan perintah shell secara interaktif langsung dari dashboard admin (PowerShell/CMD pada Windows, Bash pada Linux).
* **Task & Process Manager**: Lihat daftar proses yang sedang berjalan pada client, urutkan berdasarkan CPU & Memory, serta tombol **Kill Process** langsung dari browser.
* **Power Controls**: Kunci layar (*Lock*), *Reboot*, atau *Shutdown* client dari jarak jauh.

---

## 🏗️ Struktur Proyek (Directory Layout)

```
remotedesktop/
├── install_admin_server.bat # Installer 1-klik untuk Admin Server (Windows, Offline/Online)
├── install_admin_server.sh  # Installer untuk Admin Server (Linux/Ubuntu, Offline/Online)
├── run_server.bat           # Launcher server 1-klik untuk Windows
├── run_server.py            # Entry point server (dengan auto-check port)
├── reset_password.bat       # Script console untuk reset password admin
├── reset_password.py        # Logika reset password console
├── requirements.txt         # Daftar pustaka Python server
├── server/
│   ├── main.py              # FastAPI server, REST API, WebSockets, UDP beacon
│   ├── auth.py              # Autentikasi, hashing PBKDF2, token session
│   ├── client_manager.py    # Manajemen status client & multiplexing viewer
│   ├── port_utils.py        # Detektor ketersediaan port bebas & proses
│   ├── offline_packages/    # Bundel wheel (.whl) server offline (Win & Linux cp310)
│   ├── download_offline_packages.bat # Skrip download/update wheel server Windows
│   ├── download_offline_packages.sh  # Skrip download/update wheel server Linux
│   └── static/
│       ├── index.html       # Dashboard UI modern dengan modal Settings & Multi-View
│       ├── login.html       # Halaman Login modern (Show Pass, Remember, Setup)
│       ├── css/style.css    # Styling canvas remote & dashboard
│       └── js/
│           ├── app.js       # Logika dashboard, auth token, charts, terminal, settings
│           └── remote.js    # Canvas remote screen viewer & input handler
└── client/
    ├── install_windows.bat  # Installer 1-klik untuk Client (Windows + Autostart)
    ├── run_client.bat       # Launcher client Windows
    ├── client.py            # Agent client utama (auto-connect & streaming)
    ├── screen_capture.py    # Screen capture berkecepatan tinggi (MSS / PIL)
    ├── input_handler.py     # Simulasi mouse & keyboard lintas platform
    ├── system_info.py       # Pengambil metrik CPU, RAM, Disk, OS, & IP
    ├── requirements.txt     # Dependensi mandiri khusus client
    ├── install_linux.sh     # Installer otomatis Ubuntu 22 / Linux Mint 22
    └── run_client.sh        # Script launcher client Linux
```

---

## 🚀 Panduan Instalasi & Penggunaan (Windows)

### A. Komputer Admin (Server)

1. **Jalankan Installer Admin**:
   Klik ganda file:
   ```text
   install_admin_server.bat
   ```
   *Installer ini akan:*
   - Memeriksa instalasi Python di sistem Anda.
   - **Mode Offline Otomatis**: Mendeteksi folder `server/offline_packages` dan memasang seluruh dependensi (`fastapi`, `uvicorn`, `websockets`, `psutil`) secara offline tanpa perlu koneksi internet!
   - Menanyakan apakah ingin mengatur password admin awal sekarang (atau via web nanti).
   - Menawarkan opsi membuat shortcut di Desktop (*"LAN Remote Desktop Server"*).

2. **Jalankan Server**:
   Klik ganda shortcut Desktop atau jalankan `run_server.bat`.

3. **Buka Web Dashboard**:
   Buka browser di PC Admin: `http://localhost:8001` *(atau port yang tampil di terminal)*.
   - Masukkan password admin yang telah dibuat.
   - Anda dapat mencentang *"Remember Me"* dan melihat password dengan tombol *"Show Password"*.
   - Jika ingin mengubah pengaturan atau password di kemudian hari, klik ikon **Settings (Gear)** di navbar kanan atas.
   - Jika lupa password, jalankan file **`reset_password.bat`** di PC Server.

---

### B. Komputer Admin (Server) di Linux (Ubuntu 22 / Linux Mint 22 / Debian)

Server admin dapat berjalan di mesin Linux (bahkan pada server Linux headless/tanpa monitor):

1. **Jalankan Installer Admin Linux**:
   Buka terminal di folder proyek:
   ```bash
   chmod +x install_admin_server.sh run_server.sh reset_password.sh
   sudo ./install_admin_server.sh
   ```
   *Installer ini akan:*
   - **Bypass Apt Update Cerdas**: Memeriksa apakah `python3` dan `pip3` sudah ada di sistem. Jika sudah terpasang, installer melewati `apt-get update` sehingga aman dari benturan lock `unattended-upgrades`.
   - **Mode Offline Otomatis**: Memasang pustaka server (`fastapi`, `uvicorn`, `websockets`, `psutil`) langsung dari bundel lokal `server/offline_packages` (`manylinux2014_x86_64` Python 3.10) tanpa perlu download.
   - Menjalankan wizard setup password admin awal.
   - Menawarkan opsi memasang server sebagai **Systemd Service** (`lan-remote-server.service`), sehingga server otomatis berjalan 24/7 di latar belakang saat Linux dinyalakan/booting!
   - Otomatis membuka port firewall `ufw` jika aktif.

2. **Jalankan Server Secara Manual (Opsional jika tidak memakai systemd)**:
   ```bash
   ./run_server.sh
   ```

3. **Buka Web Dashboard**:
   Akses via browser: `http://<IP_SERVER_LINUX>:8001` (atau port yang aktif).
   - Jika lupa password di server Linux: jalankan `./reset_password.sh`.

---

### C. Komputer Klien (Windows 10 / 11) - 100% Background / Service (Nol Jendela CMD)

Client Windows dirancang khusus agar berjalan sepenuhnya di latar belakang tanpa memunculkan jendela Command Prompt / CMD hitam agar **tidak mengganggu pengguna yang sedang bekerja**.

#### 🔒 Fitur Eksekusi Senyap (Silent & Windowless):
- **Windowless Executable (`--noconsole`)**: `LANRemoteClient.exe` dikompilasi dengan subsystem GUI Windows, sehingga saat dijalankan sama sekali TIDAK MEMUNCULKAN jendela CMD atau terminal hitam.
- **Silent Batch & VBS Runner**: `run_client.bat` dan `run_client_silent.vbs` menggunakan `pythonw.exe` / `wscript.exe` untuk eksekusi tersembunyi.
- **Dukungan Lock Screen & UAC 24/7**: `install_service.bat` mendaftarkan client ke Windows Task Scheduler dengan Hak Akses Tertinggi (`/rl highest`) agar client tetap aktif bahkan saat Windows terkunci (*Win+L*).
- **System Tray & Shortcut Pengaturan**: Ikon monitor status tetap ada di System Tray dekat jam taskbar, dan shortcut *"Pengaturan Server LAN Remote"* dibuat di Desktop untuk mengganti IP/Port server sewaktu-waktu lewat antarmuka grafis.

#### Pilihan 1: Menggunakan Executable Mandiri (SANGAT DIREKOMENDASIKAN 🌟)
File `LANRemoteClient.exe` telah dibundel secara mandiri (standalone) dengan opsi GUI windowless. Komputer klien **TIDAK MEMERLUKAN Python, pip, maupun internet sama sekali**!
1. Cukup salin folder `client` (atau file `LANRemoteClient.exe` dan `config.json`) via Flashdisk / LAN Share.
2. Di komputer klien target:
   - **Mode Service / Lock Screen 24/7**: Klik kanan `install_service.bat` -> pilih *"Run as administrator"*. Klien akan langsung aktif di latar belakang (tanpa CMD) dan autostart saat PC menyala.
   - **Mode Standar**: Klik ganda `run_client.bat` atau `LANRemoteClient.exe`.
3. Klien akan langsung mendeteksi Admin Server di LAN dan terhubung!

#### Pilihan 2: Menggunakan Paket Offline Wheels (Jika ingin pakai Python)
Folder `client\offline_packages` telah berisi seluruh file `.whl` dependensi yang sudah diunduh sebelumnya:
1. Salin folder `client` ke komputer klien.
2. Klik ganda `install_windows.bat` — skrip akan otomatis mendeteksi folder `offline_packages` dan memasang pustaka tanpa mengakses internet.
3. Jalankan client via `run_client.bat` (otomatis memanggil `pythonw.exe` di latar belakang).

#### 🛠️ Alat Kontrol & Manajemen Client Windows:
- **Cek Status**: Klik ganda `status_client.bat` untuk melihat proses aktif, PID, dan status Task Scheduler.
- **Hentikan Client**: Klik ganda `stop_client.bat` untuk mematikan proses client seketika.
- **Ubah IP / Port Server**: Klik ganda shortcut *"Pengaturan Server LAN Remote"* di Desktop atau jalankan `settings.bat`.

> 💡 **Ingin rebuild file EXE?** Di PC yang ada internet/PyInstaller, cukup klik ganda file `build_client_exe.bat`. File `.exe` baru akan otomatis dibuat dengan bendera `--noconsole` dan disalin ke `client\LANRemoteClient.exe`.

---

### D. Komputer Klien di Linux Mint 22 / Ubuntu 22.04 LTS

1. Buka terminal pada PC Linux Mint / Ubuntu target.
2. Salin folder proyek dan masuk ke direktori:
   ```bash
   cd remotedesktop
   ```
3. Berikan izin eksekusi dan jalankan script instalasi:
   ```bash
   chmod +x client/install_linux.sh
   ./client/install_linux.sh
   ```
   *Script ini otomatis:*
   - **Mode Offline Otomatis**: Mendeteksi folder `client/offline_packages` dan memasang pustaka binary wheel Linux x86_64 (`pillow`, `websockets`, `psutil`, `charset-normalizer`, `pystray`, `pyautogui`, dll.) untuk Python 3.10 dan 3.12 tanpa butuh koneksi internet.
   - **Bypass Apt Cerdas**: Melewati `apt-get update` jika paket dasar sudah ada, mencegah benturan dengan `unattended-upgrades`.
   - **Shortcut Desktop Otomatis**: Menambahkan shortcut *"LAN Remote Desktop Client"* dan *"Pengaturan Server LAN Remote"* langsung ke Desktop dan Menu Aplikasi Linux.
   - **Integrasi Systemd Service (24/7)**: Otomatis memasang dan mengaktifkan service systemd `lan-remotedesktop-client` sehingga client langsung berjalan di background!

4. **Manajemen Client di Linux**:
   - Cek Status Service : `sudo systemctl status lan-remotedesktop-client`
   - Cek Status Cepat   : `./client/status_client.sh`
   - Cek Log Realtime   : `sudo journalctl -u lan-remotedesktop-client -f`
   - **Ganti IP Server (GUI)** : Dobel klik shortcut *"Pengaturan Server"* di Desktop, atau jalankan `./client/settings.sh`.
   - Restart Service    : `sudo systemctl restart lan-remotedesktop-client`
   - Hentikan Service   : `sudo systemctl stop lan-remotedesktop-client`

> 💡 **Catatan untuk Ubuntu**: Pastikan sesi login menggunakan **Xorg** (klik ikon gear di pojok kanan bawah saat login Ubuntu dan pilih *"Ubuntu on Xorg"*). Linux Mint 22 Cinnamon secara bawaan sudah menggunakan X11.

---

## 🔒 Konfigurasi Firewall LAN

Pastikan port berikut diizinkan pada firewall PC Admin (Windows Defender Firewall / `ufw`):
* **Port 8000 TCP**: Untuk Web Dashboard & WebSocket.
* **Port 8002 UDP**: Untuk Auto-Discovery Beacon antar PC di LAN.

### Di Windows (Run as Administrator di PowerShell):
```powershell
New-NetFirewallRule -DisplayName "LAN Remote Desktop Server" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "LAN Remote Desktop Discovery" -Direction Inbound -LocalPort 8002 -Protocol UDP -Action Allow
```

### Di Linux (UFW):
```bash
sudo ufw allow 8000/tcp
sudo ufw allow 8002/udp
```

---

## 🗑️ Panduan Uninstall (Pencopotan Pemasangan)

Telah disediakan skrip uninstaller mandiri yang lengkap dan bersih untuk Server maupun Client di Windows dan Linux:

### 1. Server Admin:
* **Di Windows**:
  Klik kanan dan pilih *"Run as administrator"* pada file:
  ```text
  uninstall_admin_server.bat
  ```
  *Menghentikan proses server, menghapus shortcut Desktop & Startup, menghapus aturan firewall, dan membersihkan data jika diinginkan.*
* **Di Linux (Ubuntu / Mint)**:
  Buka terminal di folder project:
  ```bash
  chmod +x uninstall_admin_server.sh
  sudo ./uninstall_admin_server.sh
  ```
  *Menghentikan dan menghapus systemd background service (`lan-remote-server.service`), menghapus aturan firewall UFW, dan membersihkan data.*

### 2. Client Agent:
* **Di Windows**:
  Klik kanan dan pilih *"Run as administrator"* pada file:
  ```text
  client\uninstall_windows.bat
  ```
  *(Atau jalankan `client\uninstall_service.bat`)*
  *Menghentikan proses client (`LANRemoteClient.exe` / Python), menghapus tugas di Task Scheduler, menghapus shortcut Startup/Desktop, dan memulihkan kebijakan Windows ke standar.*
* **Di Linux (Ubuntu / Mint)**:
  Buka terminal di folder client:
  ```bash
  chmod +x client/uninstall_linux.sh
  ./client/uninstall_linux.sh
  ```
  *Menghentikan proses client, menghapus entri autostart desktop (`~/.config/autostart`), dan menghapus konfigurasi.*

---

## 🛡️ Lisensi & Catatan Keamanan
Aplikasi ini dirancang khusus untuk pemantauan dan pengelolaan jaringan lokal (**LAN Only**). Jangan mengekspos port 8000 ke internet publik tanpa menambahkan lapisan otentikasi (VPN / HTTPS / Reverse Proxy seperti Nginx dengan Basic Auth).
