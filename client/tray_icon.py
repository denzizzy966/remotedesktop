import os
import sys
import time
import webbrowser
import threading
from PIL import Image, ImageDraw

# On Linux, configure backend for pystray before importing it
if sys.platform.startswith("linux"):
    if "PYSTRAY_BACKEND" not in os.environ:
        os.environ["PYSTRAY_BACKEND"] = "appindicator"

# Try importing pystray with backend fallback
PYSTRAY_AVAILABLE = False
try:
    import pystray
    PYSTRAY_AVAILABLE = True
except Exception:
    if sys.platform.startswith("linux"):
        try:
            os.environ["PYSTRAY_BACKEND"] = "gtk"
            import pystray
            PYSTRAY_AVAILABLE = True
        except Exception:
            try:
                os.environ["PYSTRAY_BACKEND"] = "xorg"
                import pystray
                PYSTRAY_AVAILABLE = True
            except Exception:
                PYSTRAY_AVAILABLE = False
    else:
        PYSTRAY_AVAILABLE = False

try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False



try:
    from autostart_utils import is_autostart_enabled, enable_autostart, disable_autostart
except ImportError:
    try:
        from client.autostart_utils import is_autostart_enabled, enable_autostart, disable_autostart
    except ImportError:
        is_autostart_enabled, enable_autostart, disable_autostart = None, None, None

def create_tray_image(connected=True):
    """Creates a high-contrast 64x64 icon representing the client status for both dark and light taskbars."""
    img = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Outer monitor frame (vibrant cyan/indigo stroke for high contrast on black/white panels)
    outline_color = (56, 189, 248) if connected else (148, 163, 184) # Sky-400 or Slate-400
    fill_color = (15, 23, 42) # Slate-900
    draw.rounded_rectangle([4, 6, 60, 48], radius=8, fill=fill_color, outline=outline_color, width=4)

    # Inner display screen glow
    screen_color = (30, 41, 59) if connected else (30, 41, 59)
    draw.rounded_rectangle([10, 12, 54, 42], radius=4, fill=screen_color)
    
    # Desktop signal icon / remote pulse inside monitor
    if connected:
        # Mini grid/display representation
        draw.line([16, 27, 48, 27], fill=(56, 189, 248), width=2)
        draw.line([24, 21, 40, 21], fill=(125, 211, 252), width=2)
        draw.line([20, 33, 44, 33], fill=(56, 189, 248), width=2)
    else:
        # Disconnected diagonal indicator
        draw.line([20, 20, 44, 34], fill=(239, 68, 68), width=3)
        draw.line([20, 34, 44, 20], fill=(239, 68, 68), width=3)

    # Stand neck & base
    draw.rectangle([27, 48, 37, 56], fill=(148, 163, 184))
    draw.rounded_rectangle([18, 56, 46, 60], radius=2, fill=(203, 213, 225))
    
    # Status badge (Vibrant Green = Connected, Bright Red = Reconnecting / Disconnected)
    dot_color = (34, 197, 94) if connected else (239, 68, 68)
    draw.ellipse([40, 2, 62, 24], fill=dot_color, outline=(255, 255, 255), width=3)
    return img

class ClientTrayIcon:
    def __init__(self, client):
        self.client = client
        self.icon = None
        self.connected = False
        self.server_display = "Searching..."
        self._running = False

    def is_available(self):
        return PYSTRAY_AVAILABLE

    def _on_copy_id(self, icon, item):
        if PYPERCLIP_AVAILABLE:
            try:
                pyperclip.copy(self.client.device_id)
            except Exception:
                pass

    def _on_open_dashboard(self, icon, item):
        url = None
        if self.client.server_url and "ws://" in self.client.server_url:
            url = self.client.server_url.replace("ws://", "http://").split("/ws/")[0]
        elif self.client.server_url and "wss://" in self.client.server_url:
            url = self.client.server_url.replace("wss://", "https://").split("/ws/")[0]
        
        if url:
            try:
                webbrowser.open(url)
            except Exception:
                pass

    def _on_open_settings(self, icon=None, item=None):
        """Launches settings dialog as a clean independent subprocess to avoid Tkinter/GTK thread conflicts."""
        def _launch():
            try:
                import subprocess
                if getattr(sys, 'frozen', False):
                    subprocess.Popen([sys.executable, "--settings"])
                else:
                    app_dir = os.path.dirname(os.path.abspath(__file__))
                    script_path = os.path.join(app_dir, "client.py")
                    subprocess.Popen([sys.executable, script_path, "--settings"])
            except Exception as ex:
                print(f"[Tray] Gagal membuka settings GUI: {ex}")

        threading.Thread(target=_launch, daemon=True, name="SettingsSubprocessLaunchThread").start()

    def _on_toggle_autostart(self, icon, item):
        if not is_autostart_enabled:
            return
        try:
            if is_autostart_enabled():
                disable_autostart()
                print("[Tray] Autostart Windows dinonaktifkan oleh pengguna.")
            else:
                enable_autostart()
                print("[Tray] Autostart Windows diaktifkan oleh pengguna.")
            if self.icon:
                self.icon.update_menu()
        except Exception as e:
            print(f"[Tray] Gagal mengubah status autostart: {e}")

    def _on_exit(self, icon, item):
        print("\n[Tray] User requested exit via system tray.")
        self.stop()
        os._exit(0)

    def _build_menu(self):
        autostart_label = "Mulai Otomatis saat Windows Boot" if sys.platform == "win32" else "Mulai Otomatis saat Boot (Autostart)"
        return pystray.Menu(
            pystray.MenuItem(lambda text: "LAN Remote Desktop Client", None, enabled=False),
            pystray.MenuItem(lambda text: f"Status : {'Connected' if self.connected else 'Reconnecting...'}", None, enabled=False),
            pystray.MenuItem(lambda text: f"ID     : {self.client.device_id}", None, enabled=False),
            pystray.MenuItem(lambda text: f"Server : {self.server_display}", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(autostart_label, self._on_toggle_autostart, checked=lambda item: is_autostart_enabled() if is_autostart_enabled else False),
            pystray.MenuItem("Pengaturan Server (Ganti IP/Port)...", self._on_open_settings, default=True),
            pystray.MenuItem("Buka Web Dashboard Admin", self._on_open_dashboard),
            pystray.MenuItem("Salin Device ID", self._on_copy_id),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Keluar (Exit Client)", self._on_exit)
        )

    def start(self):
        """Starts the tray icon in a dedicated daemon thread with automatic retry logic."""
        if not PYSTRAY_AVAILABLE:
            print("[Tray] Pystray / AppIndicator belum terpasang atau tidak tersedia.")
            print("[Tray] Tips: Untuk mengubah IP Server kapan saja, jalankan: ./settings.sh")
            return

        def _run_tray():
            if self._running or self.icon is not None:
                return

            max_attempts = 3
            for attempt in range(1, max_attempts + 1):
                try:
                    img = create_tray_image(connected=self.connected)
                    self.icon = pystray.Icon(
                        name="lan_remote_client",
                        icon=img,
                        title=f"LAN Remote Desktop Client ({self.server_display})",
                        menu=self._build_menu()
                    )
                    self._running = True
                    print(f"[Tray] System tray icon aktif ({os.environ.get('PYSTRAY_BACKEND', 'default')}).")
                    if sys.platform == "win32":
                        self.icon.run_detached()
                    else:
                        self.icon.run() # Dedicated thread runs event loop
                    # If run() returned cleanly or was stopped, exit loop!
                    break
                except Exception as e:
                    print(f"[Tray] Inisialisasi tray icon percobaan {attempt}/{max_attempts} gagal: {e}")
                    if self.icon:
                        try:
                            self.icon.stop()
                        except Exception:
                            pass
                    self.icon = None
                    self._running = False
                    if attempt < max_attempts:
                        time.sleep(3)

            if not self._running and self.icon is None:
                print("[Tray] Info: Tray icon tidak dapat dimuat pada desktop ini. Client tetap berjalan normal di background.")
                print("[Tray] Tips: Anda tetap bisa membuka GUI Pengaturan IP/Port kapan saja via: ./settings.sh")

        threading.Thread(target=_run_tray, daemon=True, name="TrayIconThread").start()

    def update_status(self, connected: bool, server_str: str = ""):
        """Updates the tray icon image and tooltip dynamically with throttling to prevent AppIndicator duplicates."""
        new_server_display = server_str if server_str else self.server_display

        # Throttle: avoid re-rendering or hitting AppIndicator D-Bus if nothing changed
        if getattr(self, "_last_connected", None) == connected and getattr(self, "_last_server_display", None) == new_server_display:
            return

        self.connected = connected
        self.server_display = new_server_display
        self._last_connected = connected
        self._last_server_display = new_server_display

        if self.icon and self._running:
            try:
                self.icon.icon = create_tray_image(connected)
                status_text = "Connected" if connected else "Connecting..."
                self.icon.title = f"LAN Remote Desktop - {status_text} ({self.server_display})"
            except Exception:
                pass

    def stop(self):
        self._running = False
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass
            self.icon = None
