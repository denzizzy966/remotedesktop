import os
import sys
import json
import time
import socket
import asyncio
import uuid
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

from server.client_manager import client_manager
from server.port_utils import find_available_tcp_port, find_available_udp_port
from server.auth import (
    is_setup_completed,
    verify_password,
    set_admin_password,
    create_session_token,
    verify_token,
    revoke_token,
    load_config,
    save_config
)
from client.system_info import get_primary_ip

app = FastAPI(title="LAN Remote Desktop Server & Admin Dashboard")

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
STATIC_DIR = os.path.join(BASE_DIR, "static")
GUIDE_FILE = os.path.join(ROOT_DIR, "README_INSTALLER.html")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

SERVER_CONFIG = {
    "port": 8001,
    "udp_port": 8002
}

class CommandRequest(BaseModel):
    command: str

class KillProcessRequest(BaseModel):
    pid: int

class PowerRequest(BaseModel):
    action: str  # lock, reboot, shutdown

class LoginRequest(BaseModel):
    password: str
    remember: bool = False

class SetupRequest(BaseModel):
    password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class SettingsUpdateRequest(BaseModel):
    server_name: Optional[str] = None
    session_timeout_hours: Optional[int] = None
    remember_days: Optional[int] = None

# --- Background Task: LAN UDP Broadcast Beacon ---
async def udp_beacon_loop():
    """Broadcasts a beacon every 3 seconds so clients on LAN can discover this server automatically."""
    await asyncio.sleep(1.0)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    server_ip = get_primary_ip()
    udp_port = SERVER_CONFIG["udp_port"]

    # Compute broadcast targets (global + local subnet + common multi-router subnets)
    targets = {"255.255.255.255"}
    if server_ip and "." in server_ip:
        parts = server_ip.split(".")
        if len(parts) == 4:
            targets.add(f"{parts[0]}.{parts[1]}.{parts[2]}.255")
            # Multi-subnet LAN discovery support (e.g. 192.168.5.x, 192.168.1.x)
            targets.add(f"{parts[0]}.{parts[1]}.5.255")
            targets.add(f"{parts[0]}.{parts[1]}.1.255")
            targets.add(f"{parts[0]}.{parts[1]}.0.255")

    while True:
        try:
            payload = json.dumps({
                "service": "lan_remote_desktop",
                "port": SERVER_CONFIG["port"],
                "server_ip": server_ip
            }).encode("utf-8")
            for t in targets:
                try:
                    sock.sendto(payload, (t, udp_port))
                except Exception:
                    pass
        except Exception:
            pass
        await asyncio.sleep(3.0)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(udp_beacon_loop())

# --- Frontend Routes ---
@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return HTMLResponse("<h1>LAN Remote Desktop Dashboard</h1><p>index.html not found.</p>")

@app.get("/login", response_class=HTMLResponse)
async def serve_login():
    login_file = os.path.join(STATIC_DIR, "login.html")
    if os.path.exists(login_file):
        return FileResponse(login_file)
    return HTMLResponse("<h1>Login</h1><p>login.html not found.</p>")

@app.get("/guide", response_class=HTMLResponse)
@app.get("/readme", response_class=HTMLResponse)
async def serve_guide():
    if os.path.exists(GUIDE_FILE):
        return FileResponse(GUIDE_FILE)
    return HTMLResponse("<h1>Panduan Installer</h1><p>File README_INSTALLER.html tidak ditemukan.</p>")

# --- Authentication & Settings Endpoints ---
@app.get("/api/auth/status")
async def get_auth_status():
    """Checks whether the first-time setup has been completed."""
    return {"setup_completed": is_setup_completed()}

@app.post("/api/auth/setup")
async def setup_initial_password(req: SetupRequest):
    """Sets initial admin password on fresh installation."""
    if is_setup_completed():
        raise HTTPException(status_code=400, detail="Setup has already been completed.")
    if len(req.password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters.")
    
    if set_admin_password(req.password):
        token = create_session_token(remember_me=True)
        return {"success": True, "token": token}
    raise HTTPException(status_code=500, detail="Failed to save password.")

@app.post("/api/auth/login")
async def login(req: LoginRequest):
    """Authenticates admin and issues a session token."""
    if not is_setup_completed():
        raise HTTPException(status_code=400, detail="Setup required. Please set admin password first.")
    
    if verify_password(req.password):
        token = create_session_token(remember_me=req.remember)
        return {"success": True, "token": token}
    raise HTTPException(status_code=401, detail="Incorrect admin password.")

@app.get("/api/auth/verify")
async def verify_auth_token(token: Optional[str] = None):
    """Verifies if an existing session token is valid."""
    return {"authenticated": verify_token(token)}

@app.post("/api/auth/logout")
async def logout(token: Optional[str] = None):
    """Revokes active session token."""
    if token:
        revoke_token(token)
    return {"success": True}

@app.post("/api/auth/change_password")
async def change_password(req: ChangePasswordRequest, token: Optional[str] = None):
    """Changes admin password from settings modal."""
    if not verify_token(token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not verify_password(req.current_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    if len(req.new_password) < 4:
        raise HTTPException(status_code=400, detail="New password must be at least 4 characters.")
    
    if set_admin_password(req.new_password):
        return {"success": True, "message": "Password changed successfully."}
    raise HTTPException(status_code=500, detail="Failed to change password.")

@app.get("/api/settings")
async def get_settings(token: Optional[str] = None):
    """Returns server settings for the settings modal."""
    if not verify_token(token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    cfg = load_config()
    return {
        "server_name": cfg.get("server_name", "LAN Remote Desktop Server"),
        "session_timeout_hours": cfg.get("session_timeout_hours", 24),
        "remember_days": cfg.get("remember_days", 30),
        "active_port": SERVER_CONFIG["port"],
        "active_udp_port": SERVER_CONFIG["udp_port"],
        "lan_ip": get_primary_ip()
    }

@app.post("/api/settings")
async def update_settings(req: SettingsUpdateRequest, token: Optional[str] = None):
    """Updates server settings from settings modal."""
    if not verify_token(token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    cfg = load_config()
    if req.server_name:
        cfg["server_name"] = req.server_name
    if req.session_timeout_hours is not None and req.session_timeout_hours > 0:
        cfg["session_timeout_hours"] = req.session_timeout_hours
    if req.remember_days is not None and req.remember_days > 0:
        cfg["remember_days"] = req.remember_days
    save_config(cfg)
    return {"success": True, "message": "Settings updated successfully."}

# --- REST API Endpoints ---
@app.get("/api/server_info")
async def get_server_info():
    """Returns LAN IP, port, and system information of the server."""
    ip = get_primary_ip()
    clients = client_manager.get_all_clients()
    online_count = sum(1 for c in clients if c.get("status") in ["online", "in_session"])
    return {
        "server_ip": ip,
        "port": SERVER_CONFIG["port"],
        "total_clients": len(clients),
        "online_clients": online_count,
        "hostname": socket.gethostname()
    }

@app.get("/api/clients")
async def list_clients():
    """Returns list of all registered clients with latest metrics."""
    return client_manager.get_all_clients()

@app.get("/api/client/{client_id}")
async def get_client_detail(client_id: str):
    """Returns details for a specific client."""
    client = client_manager.clients.get(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@app.post("/api/client/{client_id}/command")
async def execute_remote_command(client_id: str, req: CommandRequest):
    """Executes a shell command on target client and returns stdout/stderr."""
    req_id = str(uuid.uuid4())
    payload = {
        "type": "exec_cmd",
        "req_id": req_id,
        "command": req.command
    }
    res = await client_manager.send_request_to_client(client_id, payload, timeout=15.0)
    return res

@app.get("/api/client/{client_id}/processes")
async def get_client_processes(client_id: str, limit: int = 50):
    """Fetches real-time process list from client."""
    req_id = str(uuid.uuid4())
    payload = {
        "type": "list_processes",
        "req_id": req_id,
        "limit": limit
    }
    res = await client_manager.send_request_to_client(client_id, payload, timeout=6.0)
    return res

@app.post("/api/client/{client_id}/kill_process")
async def kill_client_process(client_id: str, req: KillProcessRequest):
    """Terminates a process on client."""
    req_id = str(uuid.uuid4())
    payload = {
        "type": "kill_process",
        "req_id": req_id,
        "pid": req.pid
    }
    res = await client_manager.send_request_to_client(client_id, payload, timeout=6.0)
    return res

@app.post("/api/client/{client_id}/power")
async def power_action(client_id: str, req: PowerRequest):
    """Executes lock, reboot, or shutdown on client."""
    payload = {
        "type": "power_action",
        "action": req.action
    }
    sent = await client_manager.send_to_client(client_id, payload)
    return {"success": sent, "action": req.action}

# --- WebSocket Endpoints ---

# 1. Client Agent WebSocket
@app.websocket("/ws/client/{client_id}")
async def websocket_client_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    print(f"[WS-Client] Client connected: {client_id}")
    try:
        while True:
            raw_data = await websocket.receive_text()
            msg = json.loads(raw_data)
            msg_type = msg.get("type")

            if msg_type == "register":
                client_manager.register_client(
                    client_id,
                    msg.get("data", {}),
                    msg.get("monitors", []),
                    websocket
                )
                await client_manager.broadcast_to_admins({
                    "type": "client_updated",
                    "client": client_manager.clients.get(client_id)
                })

            elif msg_type == "telemetry":
                client_manager.update_telemetry(
                    client_id,
                    msg.get("data", {}),
                    msg.get("thumbnail")
                )
                await client_manager.broadcast_to_admins({
                    "type": "client_telemetry",
                    "client_id": client_id,
                    "data": msg.get("data", {}),
                    "thumbnail": msg.get("thumbnail"),
                    "status": client_manager.clients.get(client_id, {}).get("status", "online")
                })

            elif msg_type == "frame":
                # Screen frame relay to active admin remote viewers
                await client_manager.forward_frame_to_viewers(client_id, msg)

            elif msg_type in ["cmd_result", "process_list", "kill_result", "power_result"]:
                req_id = msg.get("req_id")
                if req_id:
                    client_manager.resolve_pending_request(req_id, msg)

    except WebSocketDisconnect:
        print(f"[WS-Client] Client disconnected: {client_id}")
        client_manager.disconnect_client(client_id)
        await client_manager.broadcast_to_admins({
            "type": "client_disconnected",
            "client_id": client_id
        })
    except Exception as e:
        print(f"[WS-Client] Error handling client {client_id}: {e}")
        client_manager.disconnect_client(client_id)

# 2. Admin Dashboard WebSocket (Live Metrics Feed)
@app.websocket("/ws/admin/dashboard")
async def websocket_admin_dashboard_endpoint(websocket: WebSocket):
    await websocket.accept()
    client_manager.register_admin(websocket)
    try:
        # Immediately send list of all clients on connect
        await websocket.send_text(json.dumps({
            "type": "initial_state",
            "clients": client_manager.get_all_clients()
        }))
        while True:
            # Keep connection open and handle client ping/pong
            msg = await websocket.receive_text()
            if msg == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        client_manager.unregister_admin(websocket)
    except Exception:
        client_manager.unregister_admin(websocket)

# 3. Interactive Remote Desktop Viewer WebSocket
@app.websocket("/ws/admin/remote/{client_id}")
async def websocket_admin_remote_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    print(f"[WS-Remote] Admin opened remote desktop session for client: {client_id}")
    await client_manager.add_remote_viewer(client_id, websocket)
    
    # Broadcast to dashboard that this client is now in session
    await client_manager.broadcast_to_admins({
        "type": "client_status",
        "client_id": client_id,
        "status": "in_session"
    })

    try:
        while True:
            raw_msg = await websocket.receive_text()
            msg = json.loads(raw_msg)
            if msg.get("type") == "close_session":
                break
            # Forward input commands (mouse, keyboard, quality change) directly to the target client
            await client_manager.send_to_client(client_id, msg)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[WS-Remote] Remote session ended: {e}")
    finally:
        print(f"[WS-Remote] Admin closed remote desktop session for client: {client_id}")
        await client_manager.remove_remote_viewer(client_id, websocket)
        await client_manager.broadcast_to_admins({
            "type": "client_status",
            "client_id": client_id,
            "status": "online" if client_id in client_manager.client_sockets else "offline"
        })

if __name__ == "__main__":
    import uvicorn
    # Bind to 0.0.0.0 so any machine in the LAN can access
    uvicorn.run(app, host="0.0.0.0", port=8000)
