================================================================================
          PANDUAN LENGKAP INSTALASI & PENGGUNAAN (README INSTALLER)
       LAN REMOTE DESKTOP & FLEET MONITORING - WINDOWS & UBUNTU / MINT
================================================================================
* TIPS: Tersedia versi WEB HTML INTERAKTIF di file "README_INSTALLER.html"
        (Bisa diklik ganda langsung di browser dengan fitur Search & Copy Script)
        atau via browser: http://[SERVER_IP]:8001/static/guide.html
================================================================================

DAFTAR ISI:
 1. Ringkasan & Arsitektur Sistem
 2. Fitur Pengecekan Port Otomatis (Auto Port Detection)
 3. Cara Mengatur Server IP & Port pada Client
 4. Panduan Instalasi Client (Windows 10/11)
    - Opsi 1: Executable Mandiri (LANRemoteClient.exe) - Tanpa Python & Offline
    - Opsi 2: Installer Batch (install_windows.bat)
    - Opsi 3: Pemasangan Offline via Wheels (offline_packages)
    - Opsi 4: Service & Task Scheduler (install_service.bat) - Lock Screen & UAC
    - Fitur System Tray & Panduan Autostart Windows
 5. Panduan Instalasi Client (Linux Mint 22 / Ubuntu 22.04 LTS)
    - Fitur & Tampilan System Tray (Status Monitor & Menu Klik Kanan)
    - Cara Pasang Dependensi System Tray (pystray)
    - Cara Mengaktifkan Autostart (Skrip setup_autostart_linux.sh & GUI Menu)
    - Instalasi Penuh via install_linux.sh
    - Opsi Mode Headless (--no-tray)
 6. Panduan Instalasi Server Admin (Windows 10/11)
 7. Panduan Instalasi Server Admin di Ubuntu Server (Linux Headless / 24-7)
 8. Manajemen Password & Reset Console
 9. Analisis Komparasi: Di Mana Server Lebih Bagus Di-install?
10. Tanya Jawab & Troubleshooting Jaringan LAN
11. Panduan Lengkap Uninstall (Server & Client Windows/Linux)

================================================================================
1. RINGKASAN & ARSITEKTUR SISTEM
================================================================================
Aplikasi ini dirancang khusus untuk memonitor dan mengontrol komputer dalam
jaringan lokal (LAN / Wi-Fi lokal / Intranet) secara real-time:
 - Server (Admin Dashboard): Pusat kontrol web yang dapat diakses via browser
   (Chrome, Edge, Firefox). Menampilkan status PC, CPU %, RAM %, Disk %,
   live screen thumbnail, remote desktop interaktif, task manager, dan terminal.
 - Client (Agent): Berjalan ringan di latar belakang pada setiap PC target
   (Windows 10/11 dan Ubuntu 22 / Linux Mint 22).

================================================================================
2. FITUR PENGECEKAN PORT OTOMATIS (AUTO PORT DETECTION)
================================================================================
Pertanyaan: Apakah port server ini membaca / mengecek otomatis port yang kosong?
Jawaban: YA, 100% OTOMATIS!

Cara Kerja Port Checker pada Server:
 1. Saat server dijalankan (`run_server.py` / `run_server.bat` / `run_server.sh`),
    sistem secara cerdas memeriksa ketersediaan port TCP default (8000).
 2. Jika port 8000 sedang terpakai (misalnya oleh Windows Service `svchost.exe`,
    IIS, Laragon, Apache, Docker, dll), sistem TIDAK AKAN ERROR / CRASH.
 3. Server akan mendeteksi nama proses & PID yang memakai port tersebut:
    Contoh log:
    "[Port Checker] Warning: Port 8000 is ALREADY IN USE by process 'svchost.exe' (PID 5636)."
 4. Server otomatis mencari port berikutnya yang benar-benar bersih dan kosong
    (contoh: 8001, 8002, dst).
 5. Server kemudian mengaktifkan "UDP Beacon Broadcast" pada port 8002 yang secara
    berkala menyiarkan: "Halo Client di LAN, saya Server Admin aktif di Port 8001!".
 6. Hasilnya: Port yang bentrok dihindari secara otomatis tanpa intervensi manual.

================================================================================
3. CARA MENGATUR SERVER IP & PORT PADA CLIENT
================================================================================
Pertanyaan: Bagaimana cara mengatur di client waktu install menggunakan port mana
            atau server IP mana?
Jawaban: Anda memiliki 3 CARA FLEKSIBEL:

CARA A: Lewat Installer Interaktif (Sangat Direkomendasikan)
 Saat Anda menjalankan `install_windows.bat` atau `install_linux.sh`, installer
 akan menampilkan prompt interaktif:
   "Masukkan IP Server Admin (kosongkan untuk Auto-Discovery): [ketik IP, misal 192.168.1.50]"
   "Masukkan Port Server Admin (default: 8001): [ketik Port, misal 8001]"
 Nilai ini langsung disimpan ke file `config.json` di komputer client.

CARA B: Otomatis Penuh (Auto-Discovery Tanpa Perlu Ketik Apapun)
 Jika Anda menekan ENTER (kosongkan IP & Port saat instalasi):
   - Client akan menggunakan mode "Auto-Discovery".
   - Client akan mendengarkan sinyal UDP dari server di LAN.
   - Begitu server menyala di port berapa pun (8000, 8001, 8005), client akan
     langsung mendeteksi IP dan Port server secara otomatis dalam 2 detik!

CARA C: Edit Manual File `config.json`
 Di folder client terdapat file `config.json`:
   {
       "server_url": "",
       "server_ip": "192.168.1.100",
       "server_port": 8001,
       "device_id": "",
       "auto_discover": false
   }
 Anda dapat mengubah `server_ip` dan `server_port` kapan saja dengan Notepad.

CARA D: Antarmuka Grafis (UI Settings) - Paling Mudah & Praktis
 Kapan saja Anda ingin mengganti IP / Port server tanpa repot mengedit teks:
   1. Melalui System Tray:
      - Klik ganda (Double-Click) ikon monitor di System Tray taskbar, ATAU
      - Klik kanan ikon System Tray -> pilih "Pengaturan Server (Ganti IP/Port)..."
   2. Melalui Shortcut Langsung:
      - Di Windows: Klik ganda file `client/settings.bat` (atau `LANRemoteClient.exe --settings`)
      - Di Linux: Jalankan `./client/settings.sh` (atau `python3 client.py --settings`)
   Jendela pengaturan grafis modern akan terbuka. Cukup ketik IP Server baru dan
   klik tombol "Simpan & Sambungkan". Client akan otomatis menyimpan ke config.json
   dan langsung menyambungkan ulang ke server baru secara instan!

================================================================================
4. PANDUAN INSTALASI CLIENT (WINDOWS 10 / WINDOWS 11)
================================================================================

A. PILIHAN METODE INSTALASI CLIENT WINDOWS:

MODE BACKGROUND 100% SILENT (TANPA JENDELA CMD / TERMINAL):
Client Windows dirancang khusus agar berjalan sepenuhnya di latar belakang tanpa
mengganggu user:
- `LANRemoteClient.exe` dikompilasi dengan subsystem GUI (`--noconsole`) sehingga
  TIDAK AKAN PERNAH memunculkan jendela Command Prompt / CMD hitam.
- `run_client.bat` dan `run_client_silent.vbs` menggunakan runner tanpa konsol
  (`pythonw.exe` / `wscript.exe`) yang langsung menutup prompt dalam sekejap.
- Ikon status monitor tetap muncul di System Tray (dekat jam taskbar) tanpa mengganggu.
- Shortcut Desktop "Pengaturan Server LAN Remote" dibuat otomatis untuk memudahkan
  mengganti IP server kapan saja lewat antarmuka grafis.

OPSI 1: EXECUTABLE MANDIRI (LANRemoteClient.exe) - TERMUDAH & 100% OFFLINE
 Cocok untuk: PC Client yang tidak ada internet dan tidak ada Python.
 Langkah-langkah:
  1. Salin file `client/LANRemoteClient.exe` dan `client/config.json` ke PC target
     (bisa diletakkan di folder mana saja, misal `C:\Program Files\LANClient\`).
  2. Klik ganda `LANRemoteClient.exe`.
  3. Client langsung aktif di latar belakang (tanpa jendela CMD) dan terhubung ke Server Admin!

OPSI 2: MENGGUNAKAN INSTALLER BATCH (install_windows.bat)
 Cocok untuk: Instalasi terpadu dengan opsi setup shortcut & autostart otomatis.
 Langkah-langkah:
  1. Salin folder `client` ke PC target (via Flashdisk/LAN Sharing).
  2. Klik kanan `install_windows.bat` -> pilih "Run as administrator" (atau klik ganda).
  3. Installer akan memeriksa ketersediaan file `LANRemoteClient.exe`:
     - Jika ada file .exe: Langsung melompat ke konfigurasi IP/Port.
     - Jika belum ada .exe: Memasang dependensi python dari folder offline.
  4. Masukkan IP Server Admin & Port (atau tekan Enter untuk Auto-Discovery).
  5. Pilih 'Y' untuk mengaktifkan Autostart saat Windows Startup (Background/Windowless).
  6. Pilih 'Y' untuk membuat shortcut di Desktop (Client & Pengaturan Server). Selesai!

OPSI 3: PEMASANGAN OFFLINE MENGGUNAKAN WHEELS (offline_packages)
 Cocok untuk: PC yang punya Python tetapi terisolasi tanpa akses internet.
 Langkah-langkah:
  1. Di folder `client/offline_packages` sudah disediakan file-file library `.whl`
     lengkap (websockets, psutil, mss, Pillow, pynput, pyautogui, pystray, dll).
  2. Buka Command Prompt / PowerShell di folder client:
     pip install --no-index --find-links=offline_packages -r requirements.txt
  3. Jalankan client di background dengan: `run_client.bat`

OPSI 4: INSTALL SEBAGAI SERVICE / TUGAS SISTEM (install_service.bat) - REKOMENDASI TERBAIK
 Cocok untuk: PC yang ingin berjalan 24/7 di background, menembus Lock Screen & UAC.
 Langkah-langkah:
  1. Klik kanan `install_service.bat` -> pilih "Run as administrator".
  2. Script akan otomatis:
     - Mengaktifkan izin Software SAS (Ctrl+Alt+Del) di Registry Windows.
     - Menghubungkan client ke Server Admin (via IP/Port atau Auto-Discovery).
     - Mendaftarkan client ke Windows Task Scheduler dengan Hak Akses Tertinggi (`/rl highest`)
       dan target windowless (0 jendela CMD).
     - Menyalakan client di latar belakang saat itu juga.
     - Membuat shortcut "Pengaturan Server LAN Remote" di Desktop.
  3. Komputer dapat diakses dan dikontrol meskipun dalam kondisi Lock Screen (Win+L)!

MANAJEMEN CLIENT WINDOWS:
 - Cek Status Client : Klik ganda `status_client.bat` (melihat PID & status Task Scheduler)
 - Hentikan Client   : Klik ganda `stop_client.bat`
 - Ganti IP Server   : Klik ganda `settings.bat` atau shortcut Desktop "Pengaturan Server LAN Remote"

B. FITUR SYSTEM TRAY & AUTOSTART PADA WINDOWS:
 1. Tampilan System Tray Windows:
    - Client otomatis memunculkan icon monitor dengan indikator status
      di System Tray (area notifikasi dekat jam di pojok kanan bawah):
      * 🟢 Titik Hijau: Terhubung aktif ke Server Remote Desktop.
      * 🔴 Titik Merah: Disconnected / Reconnecting (mencari server).
    - Klik kanan pada icon System Tray untuk membuka menu interaktif:
      * Status koneksi (Connected / Reconnecting)
      * Device ID PC ini
      * Server IP & Port yang sedang terhubung
      * "Pengaturan Server (Ganti IP/Port)..."
      * "Salin Device ID" ke clipboard
      * "Buka Web Dashboard Admin" langsung di browser
      * "Keluar (Exit Client)"
 2. Panduan Autostart saat Windows Boot / Login:
    - Cara A (Rekomendasi - Menembus Lock Screen & Hak Admin, 100% Windowless):
      Klik kanan `install_service.bat` -> pilih "Run as administrator".
      Task Scheduler akan menyalakan client secara otomatis dengan `/rl highest`
      di background setiap kali komputer booting / user login tanpa memunculkan CMD.
    - Cara B (Standar Folder Startup Windows):
      Installer `install_windows.bat` otomatis memasukkan shortcut windowless
      ke folder Startup Windows (`shell:startup`).

================================================================================
5. PANDUAN INSTALASI CLIENT (LINUX MINT 22 / UBUNTU 22.04 LTS)
================================================================================

A. FITUR & TAMPILAN SYSTEM TRAY LINUX:
 Ikon monitor dinamis akan muncul di panel taskbar Linux Mint (Cinnamon/MATE/XFCE)
 atau top bar Ubuntu (GNOME):
  - 🟢 Titik Hijau: Terhubung aktif ke Server Remote Desktop.
  - 🔴 Titik Merah: Disconnected / Mencari server (Auto-reconnect).
  - Menu Klik Kanan pada Ikon Tray:
    * Status : Connected / Reconnecting
    * ID     : Device ID PC Linux target
    * Server : IP & Port Server Admin yang tersambung
    * Separator
    * Buka Web Dashboard Admin (otomatis membuka browser ke dashboard server)
    * Salin Device ID (menyalin ID ke clipboard)
    * Separator
    * Keluar (Exit Client)

B. CARA INSTALL DEPENDENSI SYSTEM TRAY DI LINUX:
 Buka terminal di folder client pada Linux Mint / Ubuntu:
   # 1. Pasang paket sistem untuk integrasi panel AppIndicator & Tkinter:
   sudo apt-get update
   sudo apt-get install -y python3-gi python3-gi-cairo gir1.2-ayatanaappindicator3-0.1 python3-tk

   # 2. Pasang pystray via pip:
   pip3 install pystray --break-system-packages

   # Untuk mesin offline:
   Telah disediakan wheel di folder `client/offline_packages/pystray-0.19.5-py2.py3-none-any.whl`
   pip3 install --no-index --find-links=offline_packages pystray --break-system-packages

 ===============================================================================
 PENTING: MENGAPA IKON SYSTEM TRAY TIDAK MUNCUL & CARA MENGATASINYA:
 ===============================================================================
 1. DI WINDOWS 10 / WINDOWS 11:
    - Masalah: Di Windows 11, taskbar secara default menyembunyikan ikon aplikasi
      baru ke dalam menu "Hidden Icons" (tanda panah panah atas `^` di samping jam).
    - Solusi:
      a. Klik tanda panah `^` di taskbar sebelah kanan (dekat jam). Ikon LAN Remote
         Desktop akan terlihat di sana.
      b. Agar selalu muncul di taskbar utama tanpa tersembunyi:
         Buka Windows Settings -> Personalization -> Taskbar -> Other system tray icons
         (atau Taskbar corner overflow) -> Cari "LAN Remote Desktop Client" -> Geser ke "ON".
      c. Catatan Session 0: Jika client dijalankan sebagai Windows Service tingkat kernel
         (bukan via Task Scheduler onlogon), sistem Windows memblokir tampilan GUI / Tray
         (Session 0 Isolation). Selalu gunakan `install_service.bat` (Task Scheduler)
         atau letakkan shortcut di `shell:startup`.

 2. DI LINUX MINT (CINNAMON) & UBUNTU (GNOME):
    - Masalah 1: Dijalankan dengan 'sudo' (sudo ./run_client.sh)
      Penyebab: Akun root tidak memiliki akses ke sesi DBus dan X11 desktop user!
      Solusi: JANGAN JALANKAN DENGAN SUDO. Jalankan sebagai pengguna desktop biasa:
              ./run_client.sh
    - Masalah 2: Paket AppIndicator belum terpasang.
      Penyebab: Desktop Cinnamon dan GNOME memerlukan pustaka GObject Introspection.
      Solusi: Jalankan perintah:
              sudo apt-get install -y python3-gi gir1.2-ayatanaappindicator3-0.1 python3-tk
 ===============================================================================

C. CARA MENGAKTIFKAN AUTOSTART SAAT BOOT / LOGIN DI LINUX:
 Anda memiliki 2 cara mudah:

 Cara 1: Menggunakan Skrip Otomatis (Rekomendasi Cepat):
  1. Buka Terminal di folder client.
  2. Jalankan perintah:
       chmod +x setup_autostart_linux.sh
       ./setup_autostart_linux.sh
  3. Skrip ini secara otomatis mendaftarkan file `.desktop` ke standar XDG
     Autostart di `~/.config/autostart/lan-remotedesktop-client.desktop`
     (skrip otomatis mendeteksi $SUDO_USER jika dijalankan dengan sudo).
  4. Setiap kali PC menyala dan user login ke desktop, client otomatis aktif
     di latar belakang dan ikon System Tray langsung muncul di panel bar!

 Cara 2: Melalui GUI Menu Bawaan Linux Mint:
  1. Buka Menu Linux Mint -> Cari dan buka "Startup Applications" (Aplikasi Awal Mula).
  2. Klik tombol "+" (Tambah) di bagian bawah -> pilih "Custom command".
  3. Isi form:
     - Name    : LAN Remote Desktop Client
     - Command : Klik "Browse" lalu arahkan ke file `run_client.sh`
                 (atau ketik: python3 /home/user/Downloads/remote/client/client.py)
     - Delay   : 2 (detik)
  4. Klik "Save" / Simpan.

D. INSTALASI LENGKAP VIA INSTALLER LINUX & SYSTEMD SERVICE:
 1. Salin folder `client` ke komputer Linux target.
 2. Buka Terminal di folder tersebut.
 3. Beri izin eksekusi dan jalankan script installer:
      chmod +x install_linux.sh
      ./install_linux.sh
    - FITUR OFFLINE: Folder `client/offline_packages` telah memuat seluruh binary wheel
      Linux x86_64 (`manylinux2014_x86_64`) untuk Python 3.10 (Ubuntu 22.04 LTS)
      dan Python 3.12 (Linux Mint 22 / Ubuntu 24.04).
    - Installer secara otomatis mendeteksi paket offline lokal tersebut dan memasang
      seluruh dependensi tanpa butuh koneksi internet!
 4. Masukkan IP Server Admin dan Port saat diminta (atau kosongkan untuk auto-discovery).
 5. Installer akan otomatis:
    - Menaruh shortcut Desktop: "LAN Remote Desktop Client" & "Pengaturan Server LAN Remote"
    - Menanyakan aktivasi Systemd Service (Otomatis berjalan 24/7 di latar belakang).
 
 ===============================================================================
 SYSTEMD SERVICE CLIENT (systemctl) & CEK STATUS:
 ===============================================================================
 Nama Service Systemctl : lan-remotedesktop-client
 Perintah Manajemen Service:
  - Cek Status Service  : sudo systemctl status lan-remotedesktop-client
  - Cek Log Realtime    : sudo journalctl -u lan-remotedesktop-client -f
  - Restart Service     : sudo systemctl restart lan-remotedesktop-client
  - Berhentikan Service : sudo systemctl stop lan-remotedesktop-client
  - Cek Status Cepat    : ./client/status_client.sh

 ===============================================================================
 CARA GANTI IP SERVER DARI GUI (JIKA TRAY TIDAK MUNCUL):
 ===============================================================================
 Anda tidak perlu bergantung pada System Tray untuk mengganti IP!
 Anda memiliki 2 cara sangat mudah:
 1. Melalui Shortcut Desktop:
    Dobel klik shortcut "Pengaturan Server LAN Remote" di Desktop Linux Mint / Ubuntu Anda.
 2. Melalui Terminal:
    Jalankan perintah:
      ./client/settings.sh
    Jendela GUI modern akan muncul seketika. Ketik IP Server baru dan klik "Simpan & Sambungkan".
    Client yang berjalan di latar belakang akan otomatis langsung berpindah ke IP baru!

E. OPSI MODE HEADLESS (TANPA GUI / SYSTEM TRAY):
 Jika client dipasang pada mesin Linux Server tanpa monitor/GUI desktop (X11):
   python3 client.py --no-tray
 Opsi ini menonaktifkan pembuatan ikon system tray sehingga tidak menimbulkan error
 display X11.

F. RINGKASAN FILE KOMPONEN CLIENT:
 - `client/client.py`            : Kode utama agent remote desktop client
 - `client/tray_icon.py`         : Modul pembuat ikon monitor dinamis & menu tray
 - `client/settings_ui.py`       : Jendela antarmuka grafis (GUI) ganti IP & Port
 - `client/settings.sh`          : Peluncur 1-klik GUI ganti IP Server Linux
 - `client/status_client.sh`     : Skrip inspeksi status service & proses client
 - `client/start_client.sh`      : Skrip penyala client di background
 - `client/stop_client.sh`       : Skrip penghenti client
 - `client/install_client_service.sh`   : Installer systemd service client
 - `client/uninstall_client_service.sh` : Uninstaller systemd service client
 - `client/LANRemoteClient.exe`  : Executable standalone Windows (sudah include tray)
 - `client/setup_autostart_linux.sh` : Skrip 1-klik pendaftaran autostart Linux
 - `client/run_client.sh`        : Skrip starter client Linux dengan auto DISPLAY :0
 - `client/install_service.bat`  : Skrip installer Task Scheduler Windows (Lock Screen)
 - `client/install_windows.bat`  : Skrip installer terpadu Windows
 - `client/install_linux.sh`    : Skrip installer terpadu Linux Mint & Ubuntu


================================================================================
6. PANDUAN INSTALASI SERVER ADMIN (WINDOWS 10 / 11)
================================================================================
Jika PC Administrator menggunakan Windows:
 1. Pastikan Python 3.9+ sudah terpasang.
 2. Klik ganda `install_admin_server.bat` di root project.
    - FITUR OFFLINE: Installer secara otomatis mendeteksi folder `server/offline_packages`.
      Jika folder ini ada, seluruh dependensi (FastAPI, Uvicorn, websockets, psutil)
      dipasang 100% OFFLINE tanpa perlu koneksi internet dalam hitungan detik!
    - Jika folder offline tidak ada, installer akan mengunduh dari internet secara normal.
 3. Klik ganda `run_server.bat` untuk menyalakan server.
 4. Buka browser di PC Admin dan akses:
      http://localhost:8001  (atau port yang ditampilkan di layar console)
 5. Pada saat pertama kali dibuka, sistem akan meminta Anda membuat
    Username dan Password Administrator baru.

================================================================================
7. PANDUAN INSTALASI SERVER ADMIN DI UBUNTU SERVER (LINUX HEADLESS / 24-7)
================================================================================
Pertanyaan: Apakah bisa di-install server ini di Linux Server seperti Ubuntu Server?
Jawaban: SANGAT BISA DAN SANGAT DIREKOMENDASIKAN!

Server dirancang sepenuhnya "Headless" (tidak butuh GUI desktop pada mesin server),
karena server hanya bertindak sebagai backend API, WebSocket hub, dan Web Server.

Fitur Dukungan Instalasi Offline Server Linux:
 - Telah disertakan bundel paket wheel binary Linux x86_64 (`manylinux2014_x86_64`
   untuk Python 3.10) di folder `server/offline_packages/`.
 - Installer `install_admin_server.sh` secara cerdas:
   1. Memeriksa apakah `python3` dan `pip3` sudah ada di sistem. Jika sudah ada,
      installer TIDAK AKAN menjalankan `apt-get update`, sehingga kebal terhadap
      benturan apt-lock / unattended-upgrades Ubuntu!
   2. Otomatis menggunakan parameter `--no-index --find-links` ke `server/offline_packages`
      sehingga proses instalasi pustaka selesai dalam 2 detik tanpa internet.
 - Jika ingin memperbarui/mengunduh ulang paket server di kemudian hari:
   Jalankan `./server/download_offline_packages.sh` (Linux) atau
   `server\download_offline_packages.bat` (Windows).

Langkah Instalasi di Ubuntu / Linux Server (via SSH / Console):
 1. OPSI 1: PEMASANGAN SYSTEMD SERVICE OTOMATIS (1 PERINTAH - PALING DIREKOMENDASIKAN)
    Telah disediakan skrip khusus untuk mendaftarkan dan menjalankan server sebagai
    background systemd service yang berjalan 24/7 dan otomatis aktif saat booting:
      chmod +x install_server_service.sh uninstall_server_service.sh
      sudo ./install_server_service.sh

    Skrip ini secara otomatis:
      - Menghasilkan file `/etc/systemd/system/lan-remote-server.service`
      - Mengatur user non-root aktif dan direktori kerja
      - Membuka port firewall UFW (8001/tcp, 8000/tcp, 8002/udp)
      - Mengaktifkan autostart (`systemctl enable`) dan menyalakan service sekarang

    Perintah manajemen service Linux:
      - Cek status : sudo systemctl status lan-remote-server
      - Cek log    : sudo journalctl -u lan-remote-server -f
      - Restart    : sudo systemctl restart lan-remote-server
      - Berhenti   : sudo systemctl stop lan-remote-server
      - Hapus      : sudo ./uninstall_server_service.sh

 2. OPSI 2: WIZARD LENGKAP VIA `install_admin_server.sh`
    Jika Anda ingin instalasi interaktif dari awal (termasuk reset password admin):
      chmod +x install_admin_server.sh
      sudo ./install_admin_server.sh

 3. Buka browser di komputer mana saja dalam LAN:
      http://[IP-UBUNTU-SERVER]:8001
    (Contoh: http://192.168.1.10:8001 atau http://192.168.8.251:8001)

================================================================================
8. MANAJEMEN PASSWORD & RESET CONSOLE
================================================================================
Fitur Keamanan:
 1. First-Time Setup: Saat server pertama kali dibuka di browser, Anda wajib
    membuat password admin. Password di-hash menggunakan PBKDF2-HMAC-SHA256
    dengan salt unik (100.000 iterasi).
 2. Login Page:
    - Fitur "Show/Hide Password" (ikon mata).
    - Fitur "Remember Me" (menyimpan token login aman selama 30 hari).
 3. Reset Password via Console (Jika Lupa Password):
    Jika Anda lupa password admin, Anda tidak perlu khawatir:
    - Di Windows: Klik ganda `reset_password.bat` atau jalankan:
        python reset_password.py
    - Di Linux / Ubuntu Server:
        ./reset_password.sh
    Console akan meminta Anda mengetikkan password baru dan langsung memperbarui
    file konfigurasi secara aman tanpa merusak data client.
 4. Menu Settings di Admin Dashboard:
    Admin dapat mengganti password kapan saja langsung dari tombol "Settings"
    di pojok kanan atas Dashboard.

================================================================================
9. ANALISIS KOMPARASI: DI MANA SERVER LEBIH BAGUS DI-INSTALL?
================================================================================
Pertanyaan: Lebih bagus di-install di manakah server ini?
            (Ubuntu Server vs Windows Desktop)

Berikut adalah perbandingan objektifnya:

A. JIKA DI-INSTALL DI UBUNTU SERVER (PILIHAN TERBAIK UNTUK PRODUKSI / KANTOR / LAB)
 Kelebihan:
  + Uptime 24/7 Maksimal: Ubuntu Server stabil tanpa restart paksa update Windows.
  + Hemat Sumber Daya (Resource-Friendly): Headless OS Linux hanya memakai ~100MB
    RAM untuk server ini, tanpa membebani GPU atau RAM desktop.
  + Systemd Auto-Restart: Jika listrik padam dan server menyala kembali (atau
    layanan crash), systemd langsung me-restart server otomatis tanpa perlu login user.
  + IP Address Statis Alami: Server Linux biasanya diatur dengan IP statis,
    sehingga seluruh client di jaringan LAN dapat selalu terhubung tanpa putus.
  + Keamanan: Terisolasi dalam server terpusat yang aman dari salah pencet user.
 Kapan Memilih Ubuntu Server?
  -> Jika Anda memiliki PC Server khusus / NAS / Mini PC / Proxmox / Virtual Machine
     yang selalu menyala untuk memonitor kantor, warnet, lab komputer, atau sekolah.

B. JIKA DI-INSTALL DI WINDOWS DESKTOP (PILIHAN PRAKTIS UNTUK PERSONAL / SMALL OFFICE)
 Kelebihan:
  + Sangat Praktis: Tidak perlu mesin Linux atau pengetahuan terminal Linux.
  + Cukup klik ganda `run_server.bat` di PC kerja Anda sendiri.
  + Langsung bisa membuka dashboard di browser lokal (`http://localhost:8001`).
 Kekurangan:
  - Jika PC Windows Anda dimatikan/sleep/restart update, koneksi dashboard mati.
 Kapan Memilih Windows?
  -> Jika Anda hanya ingin memantau beberapa PC saat jam kerja dari PC admin Anda,
     tanpa ingin repot menyalakan dedicated server Linux.

KESIMPULAN REKOMENDASI:
 - Untuk kestabilan 24/7 dan keandalan jaringan: UBUNTU SERVER adalah pemenang mutlak.
 - Untuk kemudahan dan fleksibilitas cepat: WINDOWS DESKTOP sangat memadai.

================================================================================
10. TANYA JAWAB & TROUBLESHOOTING JARINGAN LAN
================================================================================
Q: Mengapa server otomatis memilih port 8001 bukannya 8000?
A: Pada sistem operasi Windows tertentu, port 8000 sering kali sudah direservasi
   atau digunakan oleh service sistem `svchost.exe` atau layanan web development.
   Sistem kami secara cerdas mendeteksinya dan beralih ke port 8001 agar tidak crash.

Q: Apakah firewall Windows memblokir koneksi?
A: Saat pertama kali menjalankan server atau client, Windows Firewall mungkin
   memunculkan notifikasi pop-up. Pastikan mencentang "Private networks" dan klik
   "Allow Access".
   Jika perlu membuka port manual di Windows Server:
     netsh advfirewall firewall add rule name="LAN Remote Server" dir=in action=allow protocol=TCP localport=8001
   Di Ubuntu Server (UFW):
     sudo ufw allow 8001/tcp
     sudo ufw allow 8002/udp

Q: Apakah client membebani kinerja komputer target?
A: Sangat ringan. Screen capture menggunakan MSS (library C-binding berkecepatan
   tinggi) yang hanya mengonsumsi CPU < 2% saat idle dan < 6% saat remote stream aktif.

Q: Bagaimana jika komputer client memiliki lebih dari 1 monitor?
A: Admin Dashboard menyediakan menu dropdown pilihan monitor. Admin dapat berganti
   antara Monitor 1, Monitor 2, dst secara real-time.

Q: Mengapa jika Windows terkunci (Win+L / Sleep), remote desktop tidak bisa langsung melihat layarnya? Apakah memang seperti itu?
A: YA, SECARA STANDAR ARSITEKTUR WINDOWS MEMANG SEPERTI ITU!
   Berikut penjelasan mendalam dan solusinya:
   1. Mengapa ini terjadi (Keamanan Windows UIPI & Secure Desktop):
      - Windows memisahkan desktop menjadi dua ruangan terisolasi:
        * "Default Desktop": Ruangan tempat aplikasi pengguna biasa berjalan.
        * "Winlogon Desktop (Secure Desktop)": Ruangan tempat Layar Kunci (Lock Screen),
          Layar Login, dan prompt UAC (User Account Control) berada.
      - Sistem Operasi Windows memblokir proses biasa (non-Administrator / non-Service)
        untuk mengintip layar atau merekam tombol ketikan pada Lock Screen. Ini adalah
        fitur keamanan resmi Microsoft untuk mencegah spyware/malware mencuri password Anda.
      - FAKTA PENTING: Software komersial seperti AnyDesk dan TeamViewer versi "Portable"
        (tanpa install) JUGA MENGALAMI HAL YANG SAMA PERSIS (layar hitam / diblokir)
        jika tidak dipasang sebagai Administrator / Windows Service.

   2. Solusi Ampuh agar Bisa Mengakses Layar Kunci:
      - Solusi 1: Pasang via Installer sebagai Administrator (Rekomendasi Utama)
        Klik kanan `install_windows.bat` -> pilih "Run as administrator".
        Installer akan secara otomatis mendaftarkan client ke Windows Task Scheduler
        dengan hak akses tertinggi (`/rl highest`).
        Dengan hak ini, client memiliki izin resmi Windows untuk beralih ke
        "Winlogon Desktop", sehingga Lock Screen dapat dilihat dan dikontrol penuh!
      - Solusi 2: Gunakan Tombol "Wake Screen" & "Ctrl+Alt+Del" di Dashboard
        Di Remote Viewer dashboard sudah disediakan tombol khusus:
        * Tombol "Wake Screen": Mengirim sinyal hardware untuk membangunkan monitor
          yang sedang sleep / blank.
        * Tombol "Ctrl+Alt+Del": Membuka layar pengisian password pada Windows.
      - Solusi 3: Atur Timeout Sleep pada PC Client (Untuk PC Lab / Kantor / Kiosk)
        Jika PC client adalah komputer lab atau inventaris kantor yang ingin terus dipantau,
        matikan sleep layar di Command Prompt Administrator pada PC client:
          powercfg /change monitor-timeout-ac 0
          powercfg /change standby-timeout-ac 0

================================================================================
11. PANDUAN LENGKAP UNINSTALL (PENGHAPUSAN BERSIH SERVER & CLIENT)
================================================================================
Tersedia skrip pembersihan otomatis untuk mencopot Server dan Client secara bersih:

A. UNINSTALL SERVER ADMIN:
 1. Di Windows:
    - Klik kanan `uninstall_admin_server.bat` -> pilih "Run as administrator".
    - Skrip otomatis mematikan proses server, mencopot shortcut Desktop/Startup,
      menghapus aturan firewall, dan menawarkan opsi pembersihan config/notes.
 2. Di Linux (Ubuntu Server / Linux Mint):
    - Jalankan terminal:
        chmod +x uninstall_admin_server.sh
        sudo ./uninstall_admin_server.sh
    - Skrip otomatis menghentikan dan menghapus unit systemd (`lan-remote-server.service`),
      membersihkan aturan UFW (port 8001/8000/8002), dan menghapus data jika diinginkan.

B. UNINSTALL CLIENT AGENT:
 1. Di Windows:
    - Buka folder `client`.
    - Klik kanan `uninstall_windows.bat` (atau `uninstall_service.bat`) -> pilih "Run as administrator".
    - Skrip otomatis menghentikan `LANRemoteClient.exe` / Python, menghapus tugas di
      Task Scheduler, mencopot shortcut Startup/Desktop, dan memulihkan kebijakan sistem Windows.
 2. Di Linux (Ubuntu / Linux Mint):
    - Buka folder `client`.
    - Jalankan di terminal:
        chmod +x uninstall_linux.sh
        ./uninstall_linux.sh
    - Skrip otomatis mematikan client agent dan menghapus pendaftaran autostart
      di `~/.config/autostart/lan-remotedesktop-client.desktop`.

================================================================================
Dibuat untuk Penggunaan Jaringan Lokal (LAN) Windows 10/11 & Ubuntu 22 / Mint 22
================================================================================
