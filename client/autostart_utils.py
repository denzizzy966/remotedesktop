import os
import sys
import subprocess

def is_admin():
    """Checks whether the current process has administrative privileges."""
    if sys.platform == "win32":
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    else:
        return os.geteuid() == 0 if hasattr(os, "geteuid") else False

def get_executable_target():
    """Returns (target_path, arguments, working_dir) for autostart and shortcuts."""
    if getattr(sys, 'frozen', False):
        exe_path = os.path.abspath(sys.executable)
        return exe_path, "", os.path.dirname(exe_path)
    
    # Running from Python script
    app_dir = os.path.dirname(os.path.abspath(__file__))
    client_py = os.path.join(app_dir, "client.py")
    silent_vbs = os.path.join(app_dir, "run_client_silent.vbs")
    
    if os.path.exists(silent_vbs):
        return "wscript.exe", f'"{silent_vbs}"', app_dir

    pythonw_path = os.path.join(sys.prefix, "pythonw.exe")
    if not os.path.exists(pythonw_path):
        pythonw_path = sys.executable
    return pythonw_path, f'"{client_py}"', app_dir

def create_windows_shortcut(target, args, shortcut_path, description="", working_dir=""):
    """Creates a Windows .lnk shortcut using WScript.Shell with PowerShell fallback."""
    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        lnk = shell.CreateShortcut(shortcut_path)
        lnk.TargetPath = target
        if args:
            lnk.Arguments = args
        lnk.WorkingDirectory = working_dir or os.path.dirname(target)
        lnk.WindowStyle = 7  # Minimized / Hidden
        if description:
            lnk.Description = description
        lnk.Save()
        return True
    except Exception:
        pass

    try:
        ps_cmd = (
            f"$ws = New-Object -ComObject WScript.Shell; "
            f"$s = $ws.CreateShortcut('{shortcut_path}'); "
            f"$s.TargetPath = '{target}'; "
        )
        if args:
            ps_cmd += f"$s.Arguments = '{args}'; "
        ps_cmd += (
            f"$s.WorkingDirectory = '{working_dir or os.path.dirname(target)}'; "
            f"$s.WindowStyle = 7; "
            f"$s.Save()"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
            capture_output=True,
            timeout=5
        )
        return True
    except Exception:
        return False

def is_autostart_enabled():
    """Checks if autostart is registered in Windows Registry, Startup folder, or Linux autostart."""
    if sys.platform == "win32":
        # 1. Check HKCU Run registry key
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            val, _ = winreg.QueryValueEx(key, "LANRemoteDesktopClient")
            winreg.CloseKey(key)
            if val:
                return True
        except Exception:
            pass

        # 2. Check user Startup folder
        try:
            startup_dir = os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup")
            lnk_path = os.path.join(startup_dir, "LAN Remote Desktop Client.lnk")
            if os.path.exists(lnk_path):
                return True
        except Exception:
            pass

        # 3. Check Task Scheduler
        try:
            res = subprocess.run(["schtasks", "/query", "/tn", "LANRemoteDesktopClient"], capture_output=True, text=True, timeout=3)
            if res.returncode == 0:
                return True
        except Exception:
            pass

        return False

    elif sys.platform.startswith("linux"):
        desktop_file = os.path.expanduser("~/.config/autostart/lan-remotedesktop-client.desktop")
        if os.path.exists(desktop_file):
            return True
        # Check systemd
        try:
            res = subprocess.run(["systemctl", "--user", "is-enabled", "lan-remotedesktop-client"], capture_output=True, text=True)
            if "enabled" in res.stdout:
                return True
        except Exception:
            pass
        return False

    return False

def enable_autostart():
    """Enables automatic startup on Windows (Registry Run Key + Startup Shortcut + Task Scheduler) or Linux."""
    target, args, work_dir = get_executable_target()
    
    if sys.platform == "win32":
        success = False
        
        # 1. Register in HKCU Run Key (Foolproof, runs on user logon, requires NO admin rights)
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
            run_cmd = f'"{target}" {args}'.strip() if args else f'"{target}"'
            winreg.SetValueEx(key, "LANRemoteDesktopClient", 0, winreg.REG_SZ, run_cmd)
            winreg.CloseKey(key)
            success = True
            print(f"[Autostart] Registered in Windows Registry (HKCU Run): {run_cmd}")
        except Exception as e:
            print(f"[Autostart Warning] Failed to write HKCU Run: {e}")

        # 2. Place shortcut in Startup folder (%APPDATA%\...\Startup)
        try:
            startup_dir = os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup")
            if os.path.exists(startup_dir):
                lnk_path = os.path.join(startup_dir, "LAN Remote Desktop Client.lnk")
                create_windows_shortcut(target, args, lnk_path, "LAN Remote Desktop Client Agent", work_dir)
                success = True
                print(f"[Autostart] Created Startup shortcut: {lnk_path}")
        except Exception as e:
            print(f"[Autostart Warning] Failed to create Startup shortcut: {e}")

        # 3. Create Desktop Shortcuts if they don't exist yet
        try:
            desktop_dir = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
            if os.path.exists(desktop_dir):
                client_lnk = os.path.join(desktop_dir, "LAN Remote Desktop Client.lnk")
                if not os.path.exists(client_lnk):
                    create_windows_shortcut(target, args, client_lnk, "LAN Remote Desktop Client Agent", work_dir)

                settings_lnk = os.path.join(desktop_dir, "Pengaturan Server LAN Remote.lnk")
                if not os.path.exists(settings_lnk):
                    if getattr(sys, 'frozen', False):
                        create_windows_shortcut(target, "--settings", settings_lnk, "Pengaturan Server LAN Remote", work_dir)
                    else:
                        bat_settings = os.path.join(work_dir, "settings.bat")
                        if os.path.exists(bat_settings):
                            create_windows_shortcut(bat_settings, "", settings_lnk, "Pengaturan Server LAN Remote", work_dir)
                        else:
                            create_windows_shortcut(target, f'"{os.path.join(work_dir, "client.py")}" --settings', settings_lnk, "Pengaturan Server LAN Remote", work_dir)
        except Exception:
            pass

        # 4. If running as Administrator, also register high-privilege Task Scheduler task
        if is_admin():
            try:
                task_tr = f'"{target}" {args}'.strip() if args else f'"{target}"'
                subprocess.run(
                    ["schtasks", "/create", "/tn", "LANRemoteDesktopClient", "/tr", task_tr, "/sc", "onlogon", "/rl", "highest", "/f"],
                    capture_output=True,
                    timeout=5
                )
                print("[Autostart] Registered high-privilege Task Scheduler task (Lock screen access enabled).")
            except Exception:
                pass

        return success

    elif sys.platform.startswith("linux"):
        try:
            autostart_dir = os.path.expanduser("~/.config/autostart")
            os.makedirs(autostart_dir, exist_ok=True)
            desktop_file = os.path.join(autostart_dir, "lan-remotedesktop-client.desktop")
            content = f"""[Desktop Entry]
Type=Application
Name=LAN Remote Desktop Client
Comment=Background client agent for LAN Remote Desktop
Exec=python3 {os.path.abspath(os.path.join(os.path.dirname(__file__), 'client.py'))}
Icon=network-wired
Terminal=false
Categories=Network;Utility;
X-GNOME-Autostart-enabled=true
"""
            with open(desktop_file, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"[Autostart Error] Failed to write Linux autostart: {e}")
            return False

    return False

def disable_autostart():
    """Removes autostart entries from Windows Registry, Startup folder, and Task Scheduler."""
    if sys.platform == "win32":
        # 1. Remove HKCU Run key
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, "LANRemoteDesktopClient")
            winreg.CloseKey(key)
            print("[Autostart] Removed from HKCU Run key.")
        except Exception:
            pass

        # 2. Remove Startup shortcut
        try:
            startup_dir = os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup")
            lnk_path = os.path.join(startup_dir, "LAN Remote Desktop Client.lnk")
            if os.path.exists(lnk_path):
                os.remove(lnk_path)
                print(f"[Autostart] Removed Startup shortcut: {lnk_path}")
        except Exception:
            pass

        # 3. Delete Task Scheduler task if exists
        try:
            subprocess.run(["schtasks", "/delete", "/tn", "LANRemoteDesktopClient", "/f"], capture_output=True, timeout=5)
        except Exception:
            pass

        return True

    elif sys.platform.startswith("linux"):
        desktop_file = os.path.expanduser("~/.config/autostart/lan-remotedesktop-client.desktop")
        if os.path.exists(desktop_file):
            try:
                os.remove(desktop_file)
            except Exception:
                pass
        return True

    return False

def auto_ensure_autostart():
    """Automatically ensures autostart is active whenever the client is launched (unless explicitly disabled in config)."""
    try:
        from settings_ui import load_config
    except ImportError:
        try:
            from client.settings_ui import load_config
        except ImportError:
            load_config = None

    if load_config:
        try:
            cfg = load_config()
            # Default to autostart = True for seamless background operation
            if cfg.get("autostart", True):
                if not is_autostart_enabled():
                    print("[Autostart] Autostart belum aktif, mendaftarkan otomatis ke Windows Startup...")
                    enable_autostart()
        except Exception as e:
            print(f"[Autostart Warning] Failed checking autostart status: {e}")
    else:
        if not is_autostart_enabled():
            enable_autostart()
