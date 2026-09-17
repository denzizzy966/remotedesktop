import os
import sys
import platform
import socket
import time
import subprocess
import getpass
import psutil
import uuid

def get_primary_ip():
    """Detects the primary LAN IP address (skips localhost and virtual adapters)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        # Connect to a common local/public address (doesn't actually send packet)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        pass
    
    # Fallback: inspect network interfaces
    try:
        for iface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                    return addr.address
    except Exception:
        pass
    return "127.0.0.1"

def get_device_id():
    """Generates a stable unique hardware identifier for this device."""
    try:
        node = uuid.getnode()
        return f"node-{node:012x}"
    except Exception:
        return f"dev-{socket.gethostname()}"

def get_os_info():
    """Detects detailed OS information (Windows 10/11, Ubuntu 22, Mint 22, etc.)."""
    system = platform.system()
    release = platform.release()
    version = platform.version()
    
    if system == "Windows":
        # Windows 11 build number is >= 22000
        build = sys.getwindowsversion().build if hasattr(sys, 'getwindowsversion') else 0
        if build >= 22000:
            return "Windows 11", "windows", f"Windows 11 (Build {build})"
        elif build >= 10240:
            return "Windows 10", "windows", f"Windows 10 (Build {build})"
        else:
            return f"Windows {release}", "windows", f"Windows {release} (Build {build})"
            
    elif system == "Linux":
        distro_name = "Linux"
        try:
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release") as f:
                    lines = f.readlines()
                info = {}
                for line in lines:
                    if "=" in line:
                        k, v = line.strip().split("=", 1)
                        info[k] = v.strip('"')
                distro_name = info.get("PRETTY_NAME", info.get("NAME", "Linux"))
        except Exception:
            pass
        return distro_name, "linux", f"{distro_name} ({platform.release()})"
        
    return f"{system} {release}", system.lower(), f"{system} {release}"

def format_uptime(boot_time):
    """Formats uptime into human-readable string."""
    seconds = int(time.time() - boot_time)
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0 or days > 0:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts)

# Pre-initialize cpu_percent so first read is not 0
try:
    psutil.cpu_percent(interval=None)
except Exception:
    pass

def get_system_metrics():
    """Collects comprehensive real-time system metrics."""
    os_name, os_type, os_full = get_os_info()
    ip_addr = get_primary_ip()
    hostname = socket.gethostname()
    username = getpass.getuser()
    
    # CPU
    cpu_pct = psutil.cpu_percent(interval=None)
    cpu_count = psutil.cpu_count(logical=True)
    
    # Memory
    mem = psutil.virtual_memory()
    ram_total_gb = round(mem.total / (1024 ** 3), 1)
    ram_used_gb = round(mem.used / (1024 ** 3), 1)
    ram_pct = mem.percent
    
    # Disk (root or system drive)
    root_path = "C:\\" if os_type == "windows" else "/"
    try:
        disk = psutil.disk_usage(root_path)
        disk_total_gb = round(disk.total / (1024 ** 3), 1)
        disk_used_gb = round(disk.used / (1024 ** 3), 1)
        disk_pct = disk.percent
    except Exception:
        disk_total_gb, disk_used_gb, disk_pct = 0, 0, 0

    # Uptime
    boot_time = psutil.boot_time()
    uptime_sec = int(time.time() - boot_time)
    uptime_str = format_uptime(boot_time)

    return {
        "device_id": get_device_id(),
        "hostname": hostname,
        "username": username,
        "os_name": os_name,
        "os_type": os_type,
        "os_full": os_full,
        "ip_address": ip_addr,
        "cpu_percent": cpu_pct,
        "cpu_count": cpu_count,
        "ram_total_gb": ram_total_gb,
        "ram_used_gb": ram_used_gb,
        "ram_percent": ram_pct,
        "disk_total_gb": disk_total_gb,
        "disk_used_gb": disk_used_gb,
        "disk_percent": disk_pct,
        "uptime_seconds": uptime_sec,
        "uptime_str": uptime_str,
        "timestamp": time.time()
    }

def get_process_list(limit=60):
    """Retrieves list of active processes sorted by CPU and RAM usage."""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'status']):
        try:
            info = proc.info
            processes.append({
                "pid": info['pid'],
                "name": info['name'] or "Unknown",
                "user": info['username'] or "",
                "cpu": round(info['cpu_percent'] or 0, 1),
                "ram": round(info['memory_percent'] or 0, 1),
                "status": info['status'] or "running"
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    # Sort primarily by CPU and RAM
    processes.sort(key=lambda p: (p['cpu'], p['ram']), reverse=True)
    return processes[:limit]

def kill_process(pid: int):
    """Terminates a process by PID."""
    try:
        p = psutil.Process(pid)
        p.terminate()
        try:
            p.wait(timeout=3)
        except psutil.TimeoutExpired:
            p.kill()
        return True, f"Process {pid} terminated successfully."
    except psutil.NoSuchProcess:
        return False, f"Process {pid} does not exist."
    except psutil.AccessDenied:
        return False, f"Access denied to terminate process {pid}."
    except Exception as e:
        return False, str(e)

def execute_shell_command(command: str):
    """Executes a system shell command and returns output and returncode."""
    try:
        is_win = platform.system() == "Windows"
        shell_cmd = ["cmd.exe", "/c", command] if is_win else ["/bin/bash", "-c", command]
        
        proc = subprocess.Popen(
            shell_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False
        )
        stdout, stderr = proc.communicate(timeout=15)
        return {
            "success": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": stdout,
            "stderr": stderr
        }
    except subprocess.TimeoutExpired:
        proc.kill()
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": "Command timed out after 15 seconds."
        }
    except Exception as e:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": str(e)
        }

def execute_power_action(action: str):
    """Executes system power management actions (lock, reboot, shutdown)."""
    is_win = platform.system() == "Windows"
    try:
        if action == "lock":
            if is_win:
                subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], check=True)
            else:
                # Try common Linux lock commands
                cmds = [
                    ["loginctl", "lock-session"],
                    ["xdg-screensaver", "lock"],
                    ["gnome-screensaver-command", "-l"]
                ]
                for c in cmds:
                    try:
                        subprocess.run(c, check=True)
                        break
                    except Exception:
                        continue
            return True, "Screen locked"
            
        elif action == "reboot":
            if is_win:
                subprocess.run(["shutdown", "/r", "/t", "3", "/c", "Remote reboot initiated by admin"], check=True)
            else:
                subprocess.run(["systemctl", "reboot"], check=True)
            return True, "System reboot initiated"
            
        elif action == "shutdown":
            if is_win:
                subprocess.run(["shutdown", "/s", "/t", "3", "/c", "Remote shutdown initiated by admin"], check=True)
            else:
                subprocess.run(["systemctl", "poweroff"], check=True)
            return True, "System shutdown initiated"
            
        return False, f"Unknown action: {action}"
    except Exception as e:
        return False, str(e)
