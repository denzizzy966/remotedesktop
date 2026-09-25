import asyncio
import json
import uvicorn
import websockets
import time

from server.main import app
from server.client_manager import client_manager
from client.client import RemoteClient
from client.system_info import get_system_metrics

async def run_test():
    print("=== Starting LAN Remote Desktop Integration Test ===")
    
    # 1. Start uvicorn server in background
    config = uvicorn.Config(app=app, host="127.0.0.1", port=8099, log_level="warning")
    server = uvicorn.Server(config)
    server_task = asyncio.create_task(server.serve())
    await asyncio.sleep(1.0)
    print("[1] Server started on port 8099")

    # 2. Connect client to server
    client = RemoteClient(server_url="ws://127.0.0.1:8099/ws/client/test-node-1", auto_discover=False)
    client_task = asyncio.create_task(client.start())
    await asyncio.sleep(2.0)
    print("[2] Client connected to server")

    # 3. Verify client registration
    clients = client_manager.get_all_clients()
    print(f"[3] Registered clients count: {len(clients)}")
    assert len(clients) >= 1, "Client should be registered"
    c = clients[0]
    print(f"    - Hostname: {c['hostname']}")
    print(f"    - OS: {c['os_name']}")
    print(f"    - IP: {c['ip_address']}")
    print(f"    - Status: {c['status']}")

    # 4. Test remote shell command execution
    print("[4] Testing remote shell execution...")
    res = await client_manager.send_request_to_client(
        "test-node-1",
        {"type": "exec_cmd", "req_id": "test-req-1", "command": "echo LAN_REMOTE_SUCCESS"},
        timeout=5.0
    )
    print(f"    - Shell result: {res}")
    assert "LAN_REMOTE_SUCCESS" in res.get("result", {}).get("stdout", ""), "Command output failed"

    # 5. Test process list retrieval
    print("[5] Testing process list retrieval...")
    proc_res = await client_manager.send_request_to_client(
        "test-node-1",
        {"type": "list_processes", "req_id": "test-req-2", "limit": 5},
        timeout=10.0
    )
    procs = proc_res.get("processes", [])
    print(f"    - Retrieved {len(procs)} processes:")
    for p in procs[:3]:
        print(f"      PID {p['pid']}: {p['name']} (CPU: {p['cpu']}%, RAM: {p['ram']}%)")
    assert len(procs) > 0, "Process list should not be empty"

    # 6. Test Admin Remote Desktop WebSocket session & frame delivery
    print("[6] Testing Admin Remote Desktop session...")
    admin_received_frames = []
    async with websockets.connect("ws://127.0.0.1:8099/ws/admin/remote/test-node-1") as admin_ws:
        print("    - Admin remote viewer connected")
        # Give it a second to receive at least 1-2 frames
        for _ in range(3):
            try:
                frame_msg = await asyncio.wait_for(admin_ws.recv(), timeout=4.0)
                frame_data = json.loads(frame_msg)
                if frame_data.get("type") == "frame":
                    admin_received_frames.append(frame_data)
                    print(f"    - Received frame: {frame_data['width']}x{frame_data['height']} ({len(frame_data['data'])} bytes b64)")
                    break
            except asyncio.TimeoutError:
                break

    assert len(admin_received_frames) > 0, "Admin should receive screen frames"
    print("[6] Frame streaming verified successfully!")

    # Cleanup
    client_task.cancel()
    server.should_exit = True
    await server_task
    print("\n>>> ALL TESTS PASSED SUCCESSFULLY! <<<")

if __name__ == "__main__":
    asyncio.run(run_test())
