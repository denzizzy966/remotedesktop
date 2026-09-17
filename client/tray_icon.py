import os
import sys
import webbrowser
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

def create_tray_image(connected=True):
    """Creates a 64x64 icon representing the client status."""
    img = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Outer monitor frame
    draw.rounded_rectangle([6, 8, 58, 46], radius=7, fill=(30, 41, 59), outline=(99, 102, 241), width=3)
    # Inner display screen
    draw.rounded_rectangle([11, 13, 53, 41], radius=4, fill=(15, 23, 42))
    # Stand neck & base
    draw.rectangle([27, 46, 37, 54], fill=(148, 163, 184))
    draw.rounded_rectangle([18, 54, 46, 58], radius=2, fill=(148, 163, 184))
    
    # Status badge (Green = Connected, Amber/Red = Reconnecting / Disconnected)
    dot_color = (34, 197, 94) if connected else (239, 68, 68)
    draw.ellipse([42, 4, 60, 22], fill=dot_color, outline=(255, 255, 255), width=2)
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
