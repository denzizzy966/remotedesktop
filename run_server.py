import os
import sys
import argparse
import uvicorn

# Ensure current directory is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from server.port_utils import find_available_tcp_port, find_available_udp_port
from client.system_info import get_primary_ip
import server.main as server_main

def main():
    parser = argparse.ArgumentParser(description="LAN Remote Desktop Server & Dashboard")
    parser.add_argument("--port", type=int, default=8000, help="Preferred TCP port for Admin Dashboard (default: 8000)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host address to bind (default: 0.0.0.0)")
    parser.add_argument("--udp-port", type=int, default=8002, help="Preferred UDP port for auto-discovery beacon (default: 8002)")
    args = parser.parse_args()

    print("=" * 65, flush=True)
    print(" [LAN Remote Desktop] Checking network ports...", flush=True)
    
    # 1. Check and find available TCP port
    actual_tcp_port = find_available_tcp_port(preferred_port=args.port, host=args.host)
    
    # 2. Check and find available UDP port
    actual_udp_port = find_available_udp_port(preferred_port=args.udp_port, host=args.host)

    # 3. Update server configuration with verified free ports
    server_main.SERVER_CONFIG["port"] = actual_tcp_port
    server_main.SERVER_CONFIG["udp_port"] = actual_udp_port

    lan_ip = get_primary_ip()

    print("=" * 65, flush=True)
    print(" LAN Remote Desktop & Monitoring Server Started!", flush=True)
    print(f" -> Active TCP Port : {actual_tcp_port}", flush=True)
    print(f" -> UDP Beacon Port : {actual_udp_port}", flush=True)
    print(f" -> Local Access    : http://localhost:{actual_tcp_port}", flush=True)
    print(f" -> LAN Access      : http://{lan_ip}:{actual_tcp_port}", flush=True)
    print("=" * 65, flush=True)

    uvicorn.run(server_main.app, host=args.host, port=actual_tcp_port, reload=False)

if __name__ == "__main__":
    main()
