import os
import sys
import webbrowser
import threading
from PIL import Image, ImageDraw

# Try importing pystray
try:
    import pystray
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False

try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False

try:
    from settings_ui import open_settings_window
except ImportError:
    try:
        from client.settings_ui import open_settings_window
    except ImportError:
        open_settings_window = None

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
        if open_settings_window:
            threading.Thread(target=open_settings_window, args=(self.client,), daemon=True).start()

    def _on_exit(self, icon, item):
        print("\n[Tray] User requested exit via system tray.")
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass
        # Gracefully exit process
        os._exit(0)

    def _build_menu(self):
        return pystray.Menu(
            pystray.MenuItem(lambda text: "LAN Remote Desktop Client", None, enabled=False),
            pystray.MenuItem(lambda text: f"Status : {'Connected' if self.connected else 'Reconnecting...'}", None, enabled=False),
            pystray.MenuItem(lambda text: f"ID     : {self.client.device_id}", None, enabled=False),
            pystray.MenuItem(lambda text: f"Server : {self.server_display}", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Pengaturan Server (Ganti IP/Port)...", self._on_open_settings, default=True),
            pystray.MenuItem("Buka Web Dashboard Admin", self._on_open_dashboard),
            pystray.MenuItem("Salin Device ID", self._on_copy_id),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Keluar (Exit Client)", self._on_exit)
        )

    def start(self):
        """Starts the tray icon in a background detached thread."""
        if not PYSTRAY_AVAILABLE:
            print("[Tray] Pystray belum terpasang. Menjalankan tanpa icon system tray.")
            return

        try:
            img = create_tray_image(connected=False)
            self.icon = pystray.Icon(
                name="lan_remote_client",
                icon=img,
                title="LAN Remote Desktop Client - Disconnected",
                menu=self._build_menu()
            )
            # Run detached in a background thread
            self.icon.run_detached()
            print("[Tray] System tray icon aktif.")
        except Exception as e:
            print(f"[Tray] Gagal memuat system tray: {e}")
            self.icon = None

    def update_status(self, connected: bool, server_str: str = ""):
        """Updates the tray icon image and tooltip dynamically."""
        self.connected = connected
        if server_str:
            self.server_display = server_str
        
        if self.icon:
            try:
                self.icon.icon = create_tray_image(connected)
                status_text = "Connected" if connected else "Connecting..."
                self.icon.title = f"LAN Remote Desktop - {status_text} ({self.server_display})"
            except Exception:
                pass

    def stop(self):
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass
            self.icon = None
