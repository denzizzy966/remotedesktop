import asyncio
import json
import os
import sys
import socket
import argparse
import base64
import time
from typing import Optional
import websockets

# Determine true application directory (handles PyInstaller standalone .exe as well as .py script)
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

PARENT_DIR = os.path.dirname(APP_DIR)
for p in [APP_DIR, PARENT_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Auto-detect Linux display, Xauthority, and session D-Bus (ensures systemd / background runs have GUI access)
if sys.platform.startswith("linux"):
    if "DISPLAY" not in os.environ:
        os.environ["DISPLAY"] = ":0"
    if "XAUTHORITY" not in os.environ:
        home_path = os.path.expanduser("~")
        std_xauth = os.path.join(home_path, ".Xauthority")
        if os.path.exists(std_xauth):
            os.environ["XAUTHORITY"] = std_xauth
        else:
            try:
                uid = os.getuid()
                for cand in [f"/run/user/{uid}/gdm/Xauthority", f"/run/user/{uid}/.Xauthority"]:
                    if os.path.exists(cand):
                        os.environ["XAUTHORITY"] = cand
                        break
            except Exception:
                pass
    if "DBUS_SESSION_BUS_ADDRESS" not in os.environ:
        try:
            uid = os.getuid()
            bus_path = f"/run/user/{uid}/bus"
            if os.path.exists(bus_path):
                os.environ["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path={bus_path}"
        except Exception:
            pass
    if "PYSTRAY_BACKEND" not in os.environ:
        os.environ["PYSTRAY_BACKEND"] = "appindicator"

def get_config_file_path():
    """Finds config.json in APP_DIR, current working directory, or script directory."""
    candidates = [
        os.path.join(APP_DIR, "config.json"),
        os.path.join(os.getcwd(), "config.json"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return os.path.join(APP_DIR, "config.json")

CONFIG_FILE = get_config_file_path()
UDP_DISCOVERY_PORT = 8002

def parse_ip_address(ip_str: str) -> Optional[str]:
    """Parses IPv4 address, supporting full format (192.168.8.251) and shorthand (8.251 or 168.8.251)."""
    if not ip_str:
        return None
    raw = str(ip_str).strip()
    for prefix in ["http://", "https://", "ws://", "wss://"]:
        if raw.startswith(prefix):
            raw = raw[len(prefix):]
    if "/" in raw:
        raw = raw.split("/")[0]
    if ":" in raw:
        raw = raw.split(":")[0]
    raw = raw.strip()

    parts = raw.split(".")
    # Full 4-octet IPv4 (e.g. 192.168.8.251)
    if len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
        return ".".join(parts)

    # Shorthand 2-octet (e.g. 8.251 -> 192.168.8.251)
    if len(parts) == 2 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
        expanded = f"192.168.{parts[0]}.{parts[1]}"
        print(f"[Config] Deteksi IP singkat '{ip_str}' -> Disesuaikan otomatis menjadi '{expanded}'")
        return expanded

    # Shorthand 3-octet (e.g. 168.8.251 -> 192.168.8.251)
    if len(parts) == 3 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
        expanded = f"192.{parts[0]}.{parts[1]}.{parts[2]}"
        print(f"[Config] Deteksi IP singkat '{ip_str}' -> Disesuaikan otomatis menjadi '{expanded}'")
        return expanded

    return None

try:
    from system_info import (
        get_system_metrics,
        get_device_id,
        get_process_list,
        kill_process,
        execute_shell_command,
        execute_power_action
    )
    from screen_capture import ScreenCapture
    from input_handler import InputHandler
    from tray_icon import ClientTrayIcon
    from settings_ui import open_settings_window
    from autostart_utils import auto_ensure_autostart
except ImportError:
    from client.system_info import (
        get_system_metrics,
        get_device_id,
        get_process_list,
        kill_process,
        execute_shell_command,
        execute_power_action
    )
    from client.screen_capture import ScreenCapture
    from client.input_handler import InputHandler
    try:
        from client.tray_icon import ClientTrayIcon
    except ImportError:
        ClientTrayIcon = None
    try:
        from client.settings_ui import open_settings_window
    except ImportError:
        open_settings_window = None
    try:
        from client.autostart_utils import auto_ensure_autostart
    except ImportError:
        auto_ensure_autostart = None

class RemoteClient:
    def __init__(self, server_url=None, auto_discover=None, enable_tray=True):
        self.device_id = get_device_id()
        self.explicit_server_url = server_url is not None
        self.server_url = server_url
        self.auto_discover = auto_discover
        self.enable_tray = enable_tray
        self._last_cfg_mtime = 0
        self.ws = None
        self.loop = None
        self.screen_capture = ScreenCapture()
        self.input_handler = InputHandler()
        self.tray = ClientTrayIcon(self) if (ClientTrayIcon and enable_tray) else None
        self.streaming = False
        self.stream_task = None
        self.stream_scale = 0.75
        self.stream_quality = 60
        self.stream_fps = 20
        self.stream_monitor = 1
        self.load_config(force=True)
        if self.auto_discover is None:
            self.auto_discover = True

    def apply_new_config(self, ip: str, port: int, auto_discover: bool):
        """Called by settings UI to update config and reconnect immediately."""
        print(f"[Config] Menerapkan pengaturan baru: IP={ip}, Port={port}, AutoDiscover={auto_discover}")
        self.auto_discover = auto_discover
        if ip:
            clean_ip = parse_ip_address(ip) or ip
            self.server_url = f"ws://{clean_ip}:{port}/ws/client/{self.device_id}"
            srv_label = f"{clean_ip}:{port}"
        else:
            self.server_url = None
            srv_label = "Auto-Discovery"

        if self.tray:
            self.tray.update_status(connected=False, server_str=srv_label)

        # Trigger immediate reconnect by closing current websocket if active
        if self.ws and not self.ws.closed and self.loop and self.loop.is_running():
            try:
                asyncio.run_coroutine_threadsafe(self.ws.close(), self.loop)
            except Exception as e:
                print(f"[Config] Reconnect notice: {e}")

    def load_config(self, force=False):
        """Loads configuration from config.json if present, reloading dynamically if modified."""
        if self.explicit_server_url:
            return
        cfg_file = get_config_file_path()
        if not os.path.exists(cfg_file):
            return
        try:
            mtime = os.path.getmtime(cfg_file)
            if not force and self._last_cfg_mtime == mtime:
                return
            old_url = self.server_url
            self._last_cfg_mtime = mtime
            with open(cfg_file, "r") as f:
                cfg = json.load(f)

            # 1. Check server_ip first (takes priority so manual user edits are respected!)
            server_ip_raw = cfg.get("server_ip")
            if server_ip_raw:
                clean_ip = parse_ip_address(server_ip_raw)
                if clean_ip:
                    port = int(cfg.get("server_port", 8001))
                    self.server_url = f"ws://{clean_ip}:{port}/ws/client/{self.device_id}"
                    self.auto_discover = False
                else:
                    print(f"[Config Warning] Nilai 'server_ip' di {cfg_file} tidak valid: '{server_ip_raw}'. Contoh yang benar: 192.168.8.251")
            elif cfg.get("server_url"):
                raw_url = cfg["server_url"].strip()
                if raw_url:
                    self.server_url = raw_url
                    self.auto_discover = False
            else:
                self.server_url = None
                self.auto_discover = cfg.get("auto_discover", True)

            # 2. Guarantee that the WebSocket URL always targets THIS machine's hardware ID
            if self.server_url and "/ws/client/" in self.server_url:
                base_ws = self.server_url.split("/ws/client/")[0]
                self.server_url = f"{base_ws}/ws/client/{self.device_id}"

            # 3. Auto-discovery flag
            if "auto_discover" in cfg and not server_ip_raw:
                self.auto_discover = cfg["auto_discover"]

            if old_url != self.server_url and old_url is not None:
                print(f"[Config] Konfigurasi server diperbarui: {self.server_url or 'Auto-Discovery'}")
                if self.tray:
                    srv_str = self.server_url.split('/ws/')[0].replace('ws://', '').replace('wss://', '') if self.server_url else "Auto-Discovery"
                    self.tray.update_status(connected=False, server_str=srv_str)
        except Exception as e:
            print(f"[Config] Error reading config.json ({cfg_file}): {e}")

    def save_config(self):
        """Saves current configuration to config.json."""
        cfg_file = get_config_file_path()
        try:
            cfg = {
                "server_url": self.server_url if not self.auto_discover else "",
                "server_ip": getattr(self, "server_ip", ""),
                "server_port": getattr(self, "server_port", 8001),
                "device_id": self.device_id,
                "auto_discover": self.auto_discover
            }
            with open(cfg_file, "w") as f:
                json.dump(cfg, f, indent=4)
        except Exception as e:
            print(f"[Config] Error writing config.json: {e}")

    def discover_server(self, timeout=2.5):
        """Listens for UDP broadcast beacon from server on local network."""
        print(f"[Discovery] Searching for Remote Desktop Server on LAN (UDP port {UDP_DISCOVERY_PORT})...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, "SO_REUSEPORT"):
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except Exception:
                pass
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        except Exception:
            pass

        sock.settimeout(timeout)
        try:
            sock.bind(("0.0.0.0", UDP_DISCOVERY_PORT))
            data, addr = sock.recvfrom(2048)
            info = json.loads(data.decode("utf-8"))
            if info.get("service") == "lan_remote_desktop":
                server_ip = addr[0]
                server_port = info.get("port", 8001)
                url = f"ws://{server_ip}:{server_port}/ws/client/{self.device_id}"
                print(f"[Discovery] Found Server at {server_ip}:{server_port}!")
                return url
        except Exception:
            pass
        finally:
            sock.close()
        return None

    async def start(self):
        self.loop = asyncio.get_running_loop()
        cfg_path = get_config_file_path()
        cfg_status = "Ditemukan" if os.path.exists(cfg_path) else "Default"
        print(f"==================================================")
        print(f" LAN Remote Desktop Client Agent")
        print(f" Device ID : {self.device_id}")
        print(f" OS        : {get_system_metrics()['os_name']}")
        print(f" Local IP  : {get_system_metrics()['ip_address']}")
        print(f" Config    : {cfg_path} ({cfg_status})")
        if self.server_url:
            srv_clean = self.server_url.split('/ws/')[0]
            print(f" Target    : {srv_clean}")
        else:
            print(f" Mode      : Auto-Discovery (UDP port {UDP_DISCOVERY_PORT})")
        print(f"==================================================")

        if self.tray:
            self.tray.start()

        while True:
            # Reload configuration if modified by settings GUI or user
            self.load_config()

            target_url = None
            
            # If server_url is configured, connect to it directly!
            if self.server_url:
                target_url = self.server_url
            elif self.auto_discover:
                discovered = self.discover_server()
                if discovered:
                    target_url = discovered

            if not target_url:
                print(f"[Discovery] Server tidak ditemukan via UDP broadcast di subnet lokal.")
                print(f"            (Broadcast UDP tidak dapat melewati router / beda subnet secara otomatis).")
                print(f"            Silakan hubungkan langsung dengan menentukan IP Server Admin:")
                print(f"            -> python3 client.py --ip <IP_SERVER_ADMIN>")
                print(f"            -> Contoh: python3 client.py --ip 192.168.8.251")
                print(f"            -> Atau edit file {cfg_path} dan isi \"server_ip\": \"<IP_SERVER_ADMIN>\".")
                print(f"[Discovery] Mencoba mencari server kembali dalam 5 detik...")
                await asyncio.sleep(5)
                continue

            print(f"[Connecting] Connecting to server: {target_url}...")
            try:
                # Set max_size to 16MB to allow high-res frame transfers, open_timeout to 30s for cross-VLAN/WAN stability
                async with websockets.connect(
                    target_url,
                    open_timeout=30,
                    ping_interval=20,
                    ping_timeout=15,
                    max_size=16 * 1024 * 1024
                ) as ws:
                    self.ws = ws
                    print("[Connected] Successfully connected to Admin Server!")
                    if self.tray:
                        srv_str = target_url.split('/ws/')[0].replace('ws://', '').replace('wss://', '')
                        self.tray.update_status(connected=True, server_str=srv_str)
                    
                    # Send registration handshake
                    metrics = get_system_metrics()
                    monitors = self.screen_capture.get_monitors()
                    await ws.send(json.dumps({
                        "type": "register",
                        "device_id": self.device_id,
                        "data": metrics,
                        "monitors": monitors
                    }))

                    # Run telemetry loop & receiver loop concurrently
                    telemetry_task = asyncio.create_task(self.telemetry_loop())
                    try:
                        await self.receive_loop()
                    finally:
                        telemetry_task.cancel()
                        if self.stream_task and not self.stream_task.done():
                            self.stream_task.cancel()
                            self.streaming = False

            except (websockets.ConnectionClosed, ConnectionRefusedError, OSError) as e:
                print(f"[Disconnected] Server connection lost ({e}). Retrying in 3 seconds...")
                if self.tray:
                    self.tray.update_status(connected=False)
            except Exception as e:
                print(f"[Error] Unexpected error: {e}. Retrying in 3 seconds...")
                if self.tray:
                    self.tray.update_status(connected=False)

            await asyncio.sleep(3)

    async def telemetry_loop(self):
        """Periodically collects and sends system metrics & desktop thumbnails."""
        thumb_counter = 0
        while True:
            # Check if server configuration was changed in config.json while connected
            if self.load_config():
                print("[Config] Konfigurasi server diperbarui saat terhubung. Menyambung ulang ke target baru...")
                if self.ws and not self.ws.closed:
                    await self.ws.close()
                break

            try:
                metrics = get_system_metrics()
                payload = {
                    "type": "telemetry",
                    "device_id": self.device_id,
                    "data": metrics
                }
                
                # Send thumbnail every ~4 seconds (every 2nd loop)
                if thumb_counter % 2 == 0 and not self.streaming:
                    payload["thumbnail"] = self.screen_capture.capture_thumbnail()
                
                thumb_counter += 1
                if self.ws:
                    await self.ws.send(json.dumps(payload))
            except Exception as e:
                print(f"[Telemetry] Error sending metrics: {e}")
            
            await asyncio.sleep(2.0)

    async def screen_stream_loop(self):
        """Captures and sends desktop video frames during active remote session."""
        print(f"[Stream] Starting screen streaming (scale={self.stream_scale}, quality={self.stream_quality}, target_fps={self.stream_fps})...")
        frame_interval = 1.0 / max(5, min(60, self.stream_fps))

        while self.streaming:
            t0 = time.time()
            try:
                frame = self.screen_capture.capture_frame(
                    scale=self.stream_scale,
                    quality=self.stream_quality,
                    monitor_index=self.stream_monitor
                )
                
                # Update input handler screen dimensions
                self.input_handler.update_screen_size(frame["width"], frame["height"])
                
                # Base64 encode the JPEG frame
                b64_data = base64.b64encode(frame["bytes"]).decode("ascii")
                
                msg = {
                    "type": "frame",
                    "device_id": self.device_id,
                    "width": frame["width"],
                    "height": frame["height"],
                    "rendered_w": frame["rendered_width"],
                    "rendered_h": frame["rendered_height"],
                    "data": b64_data,
                    "timestamp": time.time()
                }
                
                if self.ws:
                    await self.ws.send(json.dumps(msg))
            except Exception as e:
                print(f"[Stream] Capture error: {e}")

            # Regulate frame rate
            elapsed = time.time() - t0
            sleep_time = max(0.005, frame_interval - elapsed)
            await asyncio.sleep(sleep_time)

        print("[Stream] Screen streaming stopped.")

    async def receive_loop(self):
        """Listens for commands and input events from Admin Server."""
        async for raw_msg in self.ws:
            try:
                msg = json.loads(raw_msg)
                msg_type = msg.get("type")

                # 1. Screen Streaming Controls
                if msg_type == "start_stream":
                    self.stream_scale = float(msg.get("scale", 0.75))
                    self.stream_quality = int(msg.get("quality", 60))
                    self.stream_fps = int(msg.get("fps", 20))
                    self.stream_monitor = int(msg.get("monitor", 1))
                    
                    self.input_handler.keep_screen_awake(True)
                    if not self.streaming:
                        self.streaming = True
                        self.stream_task = asyncio.create_task(self.screen_stream_loop())

                elif msg_type == "stop_stream":
                    self.streaming = False
                    self.input_handler.keep_screen_awake(False)
                    if self.stream_task and not self.stream_task.done():
                        self.stream_task.cancel()

                elif msg_type == "update_stream_settings":
                    if "scale" in msg:
                        self.stream_scale = float(msg["scale"])
                    if "quality" in msg:
                        self.stream_quality = int(msg["quality"])
                    if "fps" in msg:
                        self.stream_fps = int(msg["fps"])
                    if "monitor" in msg:
                        self.stream_monitor = int(msg["monitor"])

                # 2. Mouse Input
                elif msg_type == "input_mouse":
                    self.input_handler.handle_mouse(msg.get("data", {}))

                # 3. Keyboard Input
                elif msg_type == "input_key":
                    self.input_handler.handle_keyboard(msg.get("data", {}))

                # 3b. Wake & SAS Actions
                elif msg_type == "wake_screen":
                    self.input_handler.wake_display()

                elif msg_type == "ctrl_alt_del":
                    self.input_handler.send_ctrl_alt_del()

                # 4. Remote Shell Command
                elif msg_type == "exec_cmd":
                    req_id = msg.get("req_id")
                    command = msg.get("command", "")
                    res = execute_shell_command(command)
                    await self.ws.send(json.dumps({
                        "type": "cmd_result",
                        "req_id": req_id,
                        "result": res
                    }))

                # 5. Process Manager
                elif msg_type == "list_processes":
                    req_id = msg.get("req_id")
                    limit = int(msg.get("limit", 60))
                    procs = get_process_list(limit=limit)
                    await self.ws.send(json.dumps({
                        "type": "process_list",
                        "req_id": req_id,
                        "processes": procs
                    }))

                elif msg_type == "kill_process":
                    req_id = msg.get("req_id")
                    pid = int(msg.get("pid", 0))
                    ok, msg_text = kill_process(pid)
                    await self.ws.send(json.dumps({
                        "type": "kill_result",
                        "req_id": req_id,
                        "success": ok,
                        "message": msg_text
                    }))

                # 6. Power Actions (Lock, Reboot, Shutdown)
                elif msg_type == "power_action":
                    action = msg.get("action")
                    ok, detail = execute_power_action(action)
                    await self.ws.send(json.dumps({
                        "type": "power_result",
                        "action": action,
                        "success": ok,
                        "message": detail
                    }))

                # 7. Ping / Heartbeat
                elif msg_type == "ping":
                    await self.ws.send(json.dumps({"type": "pong", "time": time.time()}))

            except Exception as e:
                print(f"[Receive] Error processing server message: {e}")

CLIENT_INSTANCE_PORT = 49876
_instance_socket = None

def spawn_settings_gui():
    """Launches the settings UI in an independent subprocess to avoid GUI/thread conflicts."""
    try:
        import subprocess
        if getattr(sys, 'frozen', False):
            subprocess.Popen([sys.executable, "--settings"])
        else:
            app_dir = os.path.dirname(os.path.abspath(__file__))
            script_path = os.path.join(app_dir, "client.py")
            subprocess.Popen([sys.executable, script_path, "--settings"])
    except Exception as e:
        print(f"[Client] Gagal membuka settings GUI: {e}")

def _start_instance_listener():
    """Background listener for single-instance commands."""
    global _instance_socket
    if not _instance_socket:
        return

    import threading
    def _listen():
        while True:
            try:
                conn, _ = _instance_socket.accept()
                data = conn.recv(1024)
                if data:
                    cmd = data.decode("utf-8", errors="ignore").strip()
                    if "PING" in cmd:
                        try:
                            conn.sendall(b"LAN_REMOTE_ACK\n")
                        except Exception:
                            pass
                    if "SETTINGS" in cmd:
                        spawn_settings_gui()
                conn.close()
            except Exception:
                break

    t = threading.Thread(target=_listen, daemon=True, name="SingleInstanceListener")
    t.start()

def ensure_single_instance(args):
    """
    Ensures only one client agent runs per machine.
    If already running:
      - If --ip was passed, informs user that config was updated.
      - If normal launch or shortcut click, triggers settings GUI and exits.
    """
    global _instance_socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", CLIENT_INSTANCE_PORT))
        s.listen(5)
        _instance_socket = s
        _start_instance_listener()
        return True
    except OSError:
        # Port already in use -> Another client instance is running!
        try:
            s.close()
        except Exception:
            pass

        # Try to contact the running instance to open settings
        try:
            client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_sock.settimeout(2.0)
            client_sock.connect(("127.0.0.1", CLIENT_INSTANCE_PORT))
            client_sock.sendall(b"SETTINGS\n")
            client_sock.close()
        except Exception:
            # Fallback if listener didn't respond: spawn settings directly
            spawn_settings_gui()

        if getattr(args, "ip", None):
            print(f"[Client] LAN Remote Desktop Client sudah aktif di latar belakang.")
            print(f"[Client] Konfigurasi server diperbarui ke config.json (IP: {args.ip}).")
            print(f"[Client] Client background akan otomatis tersambung ke IP baru dalam beberapa detik.")
        else:
            print("[Client] LAN Remote Desktop Client sudah aktif di latar belakang (Single Instance).")
            print("[Client] Membuka jendela Pengaturan Server...")

        sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="LAN Remote Desktop Client Agent")
    parser.add_argument("--server", type=str, help="Server WebSocket URL (e.g. ws://192.168.8.167:8001/ws/client/xyz)")
    parser.add_argument("--ip", "-i", type=str, help="Server IP address (e.g. 192.168.8.167)")
    parser.add_argument("--port", "-p", type=int, default=None, help="Server port (default: 8001)")
    parser.add_argument("--settings", "--config-gui", action="store_true", help="Buka jendela UI Pengaturan IP / Port Server")
    parser.add_argument("--no-discover", action="store_true", help="Disable automatic LAN server discovery via UDP")
    parser.add_argument("--no-tray", action="store_true", help="Disable system tray icon (useful for headless servers)")
    args = parser.parse_args()

    if args.settings:
        if open_settings_window:
            print("[Settings] Membuka jendela pengaturan IP/Port...")
            open_settings_window()
            return
        else:
            print("[Settings Error] GUI Pengaturan tidak dapat dibuka (Tkinter tidak tersedia).")
            return

    server_url = args.server
    dev_id = get_device_id()

    if args.ip:
        clean_ip = parse_ip_address(args.ip)
        if not clean_ip:
            print(f"\n[ERROR] Format IP tidak valid: '{args.ip}'")
            print(f"        Alamat IPv4 harus terdiri dari angka yang dipisahkan titik.")
            print(f"        Contoh yang benar: 192.168.8.251 (atau singkat: 8.251).\n")
            sys.exit(1)

        port = args.port or 8001
        server_url = f"ws://{clean_ip}:{port}/ws/client/{dev_id}"
        try:
            cfg = {
                "server_url": server_url,
                "server_ip": clean_ip,
                "server_port": port,
                "device_id": dev_id,
                "auto_discover": False
            }
            target_cfg_file = get_config_file_path()
            with open(target_cfg_file, "w") as f:
                json.dump(cfg, f, indent=4)
            print(f"[Config] Disimpan ke {target_cfg_file}: Server IP = {clean_ip}, Port = {port}")
        except Exception as e:
            print(f"[Config Warning] Gagal menyimpan konfigurasi: {e}")

    # Otomatis pastikan client terdaftar di Autostart Windows / Linux saat dijalankan
    if auto_ensure_autostart:
        try:
            auto_ensure_autostart()
        except Exception as e:
            print(f"[Autostart Info] {e}")

    # Pastikan hanya 1 instance client agent yang berjalan (mencegah duplikasi tray icon / proses ganda)
    ensure_single_instance(args)

    client = RemoteClient(
        server_url=server_url,
        auto_discover=not args.no_discover and not args.ip,
        enable_tray=not args.no_tray
    )
    try:
        asyncio.run(client.start())
    except KeyboardInterrupt:
        print("\n[Client] Exiting client agent gracefully.")

if __name__ == "__main__":
    main()
