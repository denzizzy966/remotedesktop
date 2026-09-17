import socket
import psutil
from typing import Tuple, Optional

def get_process_using_port(port: int, protocol: str = "tcp") -> Optional[Tuple[int, str]]:
    """Attempts to find the PID and process name using the specified port."""
    kind = "inet4" if protocol.lower() == "tcp" else "udp4"
    try:
        for conn in psutil.net_connections(kind=kind):
            if conn.laddr and conn.laddr.port == port:
                pid = conn.pid
                pname = "Unknown"
                if pid:
                    try:
                        pname = psutil.Process(pid).name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pname = "System/Protected Process"
                return pid, pname
    except Exception:
        pass
    return None

def is_tcp_port_free(port: int, host: str = "0.0.0.0") -> bool:
    """Checks if a TCP port is free to bind."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.close()
        return True
    except OSError:
        return False

def is_udp_port_free(port: int, host: str = "0.0.0.0") -> bool:
    """Checks if a UDP port is free to bind."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.close()
        return True
    except OSError:
        return False

def find_available_tcp_port(preferred_port: int = 8000, host: str = "0.0.0.0", max_attempts: int = 100) -> int:
    """
    Checks if preferred_port is available. If occupied, iterates to find the next free port.
    Returns the free port number.
    """
    port = preferred_port
    while port < preferred_port + max_attempts:
        if is_tcp_port_free(port, host):
            if port != preferred_port:
                print(f"[Port Checker] -> Selected available TCP port: {port}", flush=True)
            return port
        
        info = get_process_using_port(port, "tcp")
        if info and info[0]:
            pid, name = info
            print(f"[Port Checker] Warning: Port {port} is ALREADY IN USE by process '{name}' (PID {pid}).", flush=True)
        else:
            print(f"[Port Checker] Warning: Port {port} is ALREADY IN USE by another service.", flush=True)
        
        port += 1

    raise RuntimeError(f"Could not find an available TCP port in range {preferred_port} - {preferred_port + max_attempts}")

def find_available_udp_port(preferred_port: int = 8002, host: str = "0.0.0.0", max_attempts: int = 50) -> int:
    """
    Checks if preferred UDP port is available. If occupied, iterates to find the next free port.
    """
    port = preferred_port
    while port < preferred_port + max_attempts:
        if is_udp_port_free(port, host):
            return port
        port += 1
    return preferred_port
