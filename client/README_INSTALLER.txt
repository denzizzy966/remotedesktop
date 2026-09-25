================================================================================
          PANDUAN LENGKAP INSTALASI & PENGGUNAAN (README INSTALLER)
       LAN REMOTE DESKTOP & FLEET MONITORING - WINDOWS & UBUNTU / MINT
================================================================================

DAFTAR ISI:
 1. Ringkasan & Arsitektur Sistem
 2. Fitur Pengecekan Port Otomatis (Auto Port Detection)
 3. Cara Mengatur Server IP & Port pada Client
 4. Panduan Instalasi Client (Windows 10/11)
    - Opsi 1: Executable Mandiri (LANRemoteClient.exe) - Tanpa Python & Offline
    - Opsi 2: Installer Batch (install_windows.bat)
    - Opsi 3: Pemasangan Offline via Wheels (offline_packages)
 5. Panduan Instalasi Client (Linux Mint 22 / Ubuntu 22.04 LTS)
 6. Panduan Instalasi Server Admin (Windows 10/11)
 7. Panduan Instalasi Server Admin di Ubuntu Server (Linux Headless / 24-7)
 8. Manajemen Password & Reset Console
 9. Analisis Komparasi: Di Mana Server Lebih Bagus Di-install?
10. Tanya Jawab & Troubleshooting Jaringan LAN

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

CARA D: Antarmuka Grafis (UI Settings) - Paling Cepat & Praktis
 Kapan saja ingin mengganti IP / Port server tanpa edit file:
   1. Melalui System Tray: Klik ganda (Double-Click) ikon monitor di System Tray taskbar
      (atau klik kanan -> Pengaturan Server).
   2. Melalui Shortcut Langsung:
      - Di Windows: Klik ganda file `settings.bat` (atau `LANRemoteClient.exe --settings`)
      - Di Linux: Jalankan `./settings.sh` (atau `python3 client.py --settings`)
   Jendela pengaturan grafis akan muncul. Ketik IP Server baru dan klik "Simpan & Sambungkan".

================================================================================
4. PANDUAN INSTALASI CLIENT (WINDOWS 10 / WINDOWS 11)
================================================================================

OPSI 1: EXECUTABLE MANDIRI (LANRemoteClient.exe) - TERMUDAH & 100% OFFLINE
 Cocok untuk: PC Client yang tidak ada internet dan tidak ada Python.
 Langkah-langkah:
  1. Salin file `client/LANRemoteClient.exe` dan `client/config.json` ke PC target
     (bisa diletakkan di folder mana saja, misal `C:\Program Files\LANClient\`).
  2. Klik ganda `LANRemoteClient.exe`.
  3. Client langsung aktif di latar belakang dan terhubung ke Server Admin!
  *(Jika ingin autostart saat PC dinyalakan, buat shortcut file .exe ini lalu
    pindahkan ke folder Startup Windows: Tekan Win+R -> ketik 'shell:startup')*

OPSI 2: MENGGUNAKAN INSTALLER BATCH (install_windows.bat)
 Cocok untuk: Instalasi terpadu dengan opsi setup shortcut & autostart otomatis.
 Langkah-langkah:
  1. Salin folder `client` ke PC target (via Flashdisk/LAN Sharing).
  2. Klik kanan `install_windows.bat` -> pilih "Run as administrator" (atau klik ganda).
  3. Installer akan memeriksa ketersediaan file `LANRemoteClient.exe`:
     - Jika ada file .exe: Langsung melompat ke konfigurasi IP/Port.
     - Jika belum ada .exe: Memasang dependensi python dari folder offline.
  4. Masukkan IP Server Admin & Port (atau tekan Enter untuk Auto-Discovery).
  5. Pilih 'Y' untuk mengaktifkan Autostart saat Windows Startup.
  6. Pilih 'Y' untuk membuat shortcut di Desktop. Selesai!

OPSI 3: PEMASANGAN OFFLINE MENGGUNAKAN WHEELS (offline_packages)
 Cocok untuk: PC yang punya Python tetapi terisolasi tanpa akses internet.
 Langkah-langkah:
  1. Di folder `client/offline_packages` sudah disediakan file-file library `.whl`
     lengkap (websockets, psutil, mss, Pillow, pynput, pyautogui, dll).
  2. Buka Command Prompt / PowerShell di folder client:
     pip install --no-index --find-links=offline_packages -r requirements.txt
  3. Jalankan client dengan: `run_client.bat`

OPSI 4: INSTALL SEBAGAI SERVICE / TUGAS SISTEM (install_service.bat) - DUKUNGAN LOCK SCREEN & UAC
 Cocok untuk: PC yang sering di-lock (Win+L) dan ingin bisa diakses 100% seperti AnyDesk/RustDesk.
 Langkah-langkah:
  1. Klik kanan `install_service.bat` -> pilih "Run as administrator".
  2. Script akan otomatis:
     - Mengaktifkan izin Software SAS (Ctrl+Alt+Del) di Registry Windows.
     - Menghubungkan client ke Server Admin (via IP/Port atau Auto-Discovery).
     - Mendaftarkan client ke Windows Task Scheduler dengan Hak Akses Tertinggi (`/rl highest`).
     - Menyalakan client di latar belakang saat itu juga.
  3. Sekarang komputer dapat diakses dan dikontrol meskipun dalam kondisi Lock Screen!

================================================================================
5. PANDUAN INSTALASI CLIENT (LINUX MINT 22 / UBUNTU 22.04 LTS)
================================================================================
Langkah-langkah:
 1. Salin folder `client` ke komputer Linux target.
 2. Buka Terminal di folder tersebut.
 3. Beri izin eksekusi dan jalankan script installer:
      chmod +x install_linux.sh
      ./install_linux.sh
 4. Masukkan IP Server Admin dan Port saat diminta (atau kosongkan untuk auto-discovery).
 5. Installer akan mengonfigurasi autostart desktop secara otomatis di
    `~/.config/autostart/lan-remotedesktop-client.desktop`.
 6. Untuk menjalankan manual kapan saja:
      ./run_client.sh

================================================================================
6. PANDUAN INSTALASI SERVER ADMIN (WINDOWS 10 / 11)
================================================================================
Jika PC Administrator menggunakan Windows:
 1. Pastikan Python 3.9+ sudah terpasang.
 2. Klik ganda `install_admin_server.bat` di root project.
    Script ini akan memasang pustaka server (FastAPI, Uvicorn, websockets, dll).
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

Langkah Instalasi di Ubuntu Server (via SSH / Console):
 1. Upload/git clone folder project ke Ubuntu Server:
      scp -r remotedesktop user@192.168.1.10:/opt/remotedesktop
      cd /opt/remotedesktop
 2. Jalankan script installer otomatis untuk Linux:
      chmod +x install_admin_server.sh
      sudo ./install_admin_server.sh
 3. Script ini akan:
    - Memasang python3, python3-pip, python3-venv.
    - Menginstal requirements server.
    - Menawarkan opsi pembuatan Systemd Service otomatis (24/7 background service).
 4. Jika Anda memilih 'Y' pada opsi Systemd:
    Server akan berjalan otomatis saat Ubuntu Server booting:
      sudo systemctl start lan-remotedesktop
      sudo systemctl status lan-remotedesktop
      sudo systemctl enable lan-remotedesktop  (otomatis nyala saat boot)
 5. Buka browser di komputer mana saja dalam LAN:
      http://[IP-UBUNTU-SERVER]:8001
    (Contoh: http://192.168.1.10:8001)

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
Dibuat untuk Penggunaan Jaringan Lokal (LAN) Windows 10/11 & Ubuntu 22 / Mint 22
================================================================================
