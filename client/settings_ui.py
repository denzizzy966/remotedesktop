import os
import sys
import json
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser

# Determine application directory
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

def get_config_path():
    candidates = [
        os.path.join(APP_DIR, "config.json"),
        os.path.join(os.getcwd(), "config.json"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return os.path.join(APP_DIR, "config.json")

def load_config():
    p = get_config_path()
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "server_url": "",
        "server_ip": "192.168.8.251",
        "server_port": 8001,
        "device_id": "",
        "auto_discover": False
    }

def save_config(cfg):
    p = get_config_path()
    try:
        with open(p, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4)
        return True, p
    except Exception as e:
        return False, str(e)

_active_settings_window = None

def open_settings_window(client=None, on_saved_callback=None):
    """Opens a modern settings dialog to configure Server IP and Port."""
    global _active_settings_window
    if _active_settings_window is not None:
        try:
            _active_settings_window.deiconify()
            _active_settings_window.attributes("-topmost", True)
            _active_settings_window.lift()
            _active_settings_window.focus_force()
            _active_settings_window.after(300, lambda: _active_settings_window.attributes("-topmost", False))
            return
        except Exception:
            _active_settings_window = None

    cfg = load_config()

    try:
        root = tk.Tk()
    except Exception:
        try:
            root = tk.Toplevel()
        except Exception:
            root = tk.Tk()

    _active_settings_window = root
    root.title("Pengaturan Koneksi - LAN Remote Client")
    root.geometry("460x520")
    root.resizable(False, False)
    root.configure(bg="#0f172a") # Slate-900

    # Center window on screen
    root.update_idletasks()
    x = (root.winfo_screenwidth() - 460) // 2
    y = (root.winfo_screenheight() - 520) // 2
    root.geometry(f"+{x}+{y}")

    # Bring to top and focus
    try:
        root.attributes("-topmost", True)
        root.lift()
        root.focus_force()
        root.after(300, lambda: root.attributes("-topmost", False))
    except Exception:
        pass

    def on_window_close():
        global _active_settings_window
        _active_settings_window = None
        try:
            root.destroy()
        except Exception:
            pass

    root.protocol("WM_DELETE_WINDOW", on_window_close)

    # Styling
    style = ttk.Style()
    style.theme_use("clam")

    # Header frame
    header_frame = tk.Frame(root, bg="#1e293b", padx=20, pady=15)
    header_frame.pack(fill="x")

    lbl_title = tk.Label(header_frame, text="Pengaturan Server LAN", font=("Segoe UI", 13, "bold"), fg="#f8fafc", bg="#1e293b")
    lbl_title.pack(anchor="w")
    lbl_sub = tk.Label(header_frame, text="Konfigurasi IP & Port Server Admin Dashboard", font=("Segoe UI", 9), fg="#94a3b8", bg="#1e293b")
    lbl_sub.pack(anchor="w", pady=(2, 0))

    # Body frame
    body = tk.Frame(root, bg="#0f172a", padx=20, pady=15)
    body.pack(fill="both", expand=True)

    # Status Row
    status_frame = tk.Frame(body, bg="#1e293b", padx=12, pady=8, highlightbackground="#334155", highlightthickness=1)
    status_frame.pack(fill="x", pady=(0, 15))

    current_status = "Terhubung" if (client and getattr(client, "ws", None) and not client.ws.closed) else "Tidak Terhubung"
    status_color = "#22c55e" if current_status == "Terhubung" else "#f59e0b"

    tk.Label(status_frame, text="Status Koneksi :", font=("Segoe UI", 9, "bold"), fg="#cbd5e1", bg="#1e293b").pack(side="left")
    lbl_stat_val = tk.Label(status_frame, text=f" ● {current_status}", font=("Segoe UI", 9, "bold"), fg=status_color, bg="#1e293b")
    lbl_stat_val.pack(side="left", padx=5)

    # Server IP
    tk.Label(body, text="Alamat IP Server Admin:", font=("Segoe UI", 9, "bold"), fg="#e2e8f0", bg="#0f172a").pack(anchor="w")
    entry_ip = tk.Entry(body, font=("Segoe UI", 10), bg="#020617", fg="#38bdf8", insertbackground="#38bdf8", relief="flat", highlightbackground="#334155", highlightthickness=1)
    entry_ip.pack(fill="x", ipady=5, pady=(4, 2))
    entry_ip.insert(0, str(cfg.get("server_ip") or ""))

    tk.Label(body, text="Contoh: 192.168.8.251 (IP komputer yang menjalankan Server)", font=("Segoe UI", 8), fg="#64748b", bg="#0f172a").pack(anchor="w", pady=(0, 10))

    # Server Port
    tk.Label(body, text="Port Server Admin (Default 8001):", font=("Segoe UI", 9, "bold"), fg="#e2e8f0", bg="#0f172a").pack(anchor="w")
    entry_port = tk.Entry(body, font=("Segoe UI", 10), bg="#020617", fg="#38bdf8", insertbackground="#38bdf8", relief="flat", highlightbackground="#334155", highlightthickness=1)
    entry_port.pack(fill="x", ipady=5, pady=(4, 2))
    entry_port.insert(0, str(cfg.get("server_port") or 8001))

    tk.Label(body, text="Port HTTP/WebSocket yang aktif pada server (biasanya 8001 atau 8000)", font=("Segoe UI", 8), fg="#64748b", bg="#0f172a").pack(anchor="w", pady=(0, 10))

    # Auto-Discovery Checkbox
    var_autodiscover = tk.BooleanVar(value=bool(cfg.get("auto_discover", False)))
    chk_auto = tk.Checkbutton(
        body,
        text="Cari otomatis server di LAN (UDP Broadcast Discovery)",
        variable=var_autodiscover,
        font=("Segoe UI", 9),
        fg="#cbd5e1",
        bg="#0f172a",
        selectcolor="#020617",
        activebackground="#0f172a",
        activeforeground="#ffffff"
    )
    chk_auto.pack(anchor="w", pady=(0, 12))

    # Device ID Display
    dev_id = (client.device_id if client else cfg.get("device_id")) or "Unknown"
    dev_frame = tk.Frame(body, bg="#020617", padx=10, pady=6, highlightbackground="#1e293b", highlightthickness=1)
    dev_frame.pack(fill="x", pady=(0, 15))
    tk.Label(dev_frame, text=f"Device ID : {dev_id}", font=("Consolas", 8), fg="#94a3b8", bg="#020617").pack(side="left")

    def copy_device_id():
        root.clipboard_clear()
        root.clipboard_append(dev_id)
        messagebox.showinfo("Tersalin", f"Device ID '{dev_id}' berhasil disalin ke clipboard.")

    btn_copy = tk.Button(dev_frame, text="Salin ID", font=("Segoe UI", 8), bg="#1e293b", fg="#cbd5e1", relief="flat", cursor="hand2", command=copy_device_id)
    btn_copy.pack(side="right")

    # Action Buttons
    def save_and_apply():
        ip_val = entry_ip.get().strip()
        port_val = entry_port.get().strip()
        auto_val = var_autodiscover.get()

        if not ip_val and not auto_val:
            messagebox.showerror("Error", "Harap masukkan IP Server Admin atau centang Auto-Discovery.")
            return

        if port_val:
            try:
                p_int = int(port_val)
                if p_int < 1 or p_int > 65535:
                    raise ValueError()
            except ValueError:
                messagebox.showerror("Error", "Port tidak valid. Harus berupa angka 1 - 65535.")
                return
        else:
            p_int = 8001

        # Clean IP
        for prefix in ["http://", "https://", "ws://", "wss://"]:
            if ip_val.startswith(prefix):
                ip_val = ip_val[len(prefix):]
        if ":" in ip_val:
            ip_val = ip_val.split(":")[0]
        if "/" in ip_val:
            ip_val = ip_val.split("/")[0]

        cfg["server_ip"] = ip_val
        cfg["server_port"] = p_int
        cfg["auto_discover"] = auto_val
        if ip_val:
            cfg["server_url"] = f"ws://{ip_val}:{p_int}/ws/client/{dev_id}"
        else:
            cfg["server_url"] = ""

        ok, msg = save_config(cfg)
        if not ok:
            messagebox.showerror("Error", f"Gagal menyimpan config: {msg}")
            return

        messagebox.showinfo(
            "Berhasil",
            f"Pengaturan berhasil disimpan ke config.json!\n\nTarget Server: {ip_val}:{p_int}\nClient akan otomatis menyambung ulang."
        )

        # Notify running client if present
        if client:
            try:
                if hasattr(client, "apply_new_config"):
                    client.apply_new_config(ip_val, p_int, auto_val)
            except Exception as e:
                print(f"[Settings] Error notifying client: {e}")

        if on_saved_callback:
            try:
                on_saved_callback(cfg)
            except Exception:
                pass

        on_window_close()

    def open_web():
        ip_val = entry_ip.get().strip() or "localhost"
        port_val = entry_port.get().strip() or "8001"
        for prefix in ["http://", "https://", "ws://", "wss://"]:
            if ip_val.startswith(prefix):
                ip_val = ip_val[len(prefix):]
        webbrowser.open(f"http://{ip_val}:{port_val}")

    btn_frame = tk.Frame(root, bg="#1e293b", padx=20, pady=12)
    btn_frame.pack(fill="x", side="bottom")

    btn_web = tk.Button(btn_frame, text="Buka Web Admin", font=("Segoe UI", 9), bg="#334155", fg="#f1f5f9", relief="flat", cursor="hand2", padx=10, pady=5, command=open_web)
    btn_web.pack(side="left")

    btn_cancel = tk.Button(btn_frame, text="Batal", font=("Segoe UI", 9), bg="#1e293b", fg="#94a3b8", relief="flat", cursor="hand2", padx=12, pady=5, command=on_window_close)
    btn_cancel.pack(side="right", padx=(6, 0))

    btn_save = tk.Button(btn_frame, text="Simpan & Sambungkan", font=("Segoe UI", 9, "bold"), bg="#4f46e5", fg="#ffffff", relief="flat", cursor="hand2", padx=14, pady=5, command=save_and_apply)
    btn_save.pack(side="right")

    try:
        root.mainloop()
    except Exception:
        pass
    finally:
        _active_settings_window = None

if __name__ == "__main__":
    open_settings_window()
