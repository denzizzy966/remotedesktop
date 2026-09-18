import os
import time
import asyncio
import json
from typing import Dict, Set, Any
from fastapi import WebSocket

NOTES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "device_notes.json")

def load_device_notes() -> Dict[str, Dict[str, Any]]:
    if os.path.exists(NOTES_FILE):
        try:
            with open(NOTES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[ClientManager] Error loading device notes: {e}")
    return {}

def save_device_notes(notes: Dict[str, Dict[str, Any]]):
    try:
        with open(NOTES_FILE, "w", encoding="utf-8") as f:
            json.dump(notes, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"[ClientManager] Error saving device notes: {e}")

class ClientManager:
    def __init__(self):
        # All known clients: client_id -> dict of info & metrics
        self.clients: Dict[str, Dict[str, Any]] = {}
        # Client WebSocket connections: client_id -> WebSocket
        self.client_sockets: Dict[str, WebSocket] = {}
        # Connected Admin Dashboard WebSockets
        self.admin_dashboard_sockets: Set[WebSocket] = set()
        # Active remote session viewers: client_id -> Set[WebSocket]
        self.remote_viewers: Dict[str, Set[WebSocket]] = {}
        # Pending request futures: req_id -> asyncio.Future
        self.pending_requests: Dict[str, asyncio.Future] = {}
        # Persistent custom notes and aliases: client_id -> {"alias": str, "note": str, ...}
        self.device_notes: Dict[str, Dict[str, Any]] = load_device_notes()

    def register_client(self, client_id: str, data: dict, monitors: list, ws: WebSocket):
        """Registers or reconnects a client."""
        self.client_sockets[client_id] = ws
        now = time.time()
        
        existing = self.clients.get(client_id, {})
        note_meta = self.device_notes.get(client_id, {})
        alias = note_meta.get("alias") or existing.get("alias", "")
        note = note_meta.get("note") or existing.get("note", "")

        # Update saved device metadata
        self.device_notes[client_id] = {
            "alias": alias,
            "note": note,
            "hostname": data.get("hostname", "Unknown"),
            "username": data.get("username", ""),
            "os_name": data.get("os_name", "Unknown"),
            "os_type": data.get("os_type", "unknown"),
            "ip_address": data.get("ip_address", "127.0.0.1"),
            "last_seen": now
        }
        save_device_notes(self.device_notes)

        self.clients[client_id] = {
            "device_id": client_id,
            "alias": alias,
            "note": note,
            "hostname": data.get("hostname", "Unknown"),
            "username": data.get("username", ""),
            "os_name": data.get("os_name", "Unknown"),
            "os_type": data.get("os_type", "unknown"),
            "os_full": data.get("os_full", ""),
            "ip_address": data.get("ip_address", "127.0.0.1"),
            "status": "online",
            "last_seen": now,
            "connected_at": existing.get("connected_at", now),
            "metrics": data,
            "thumbnail": existing.get("thumbnail", ""),
            "monitors": monitors or existing.get("monitors", [])
        }

    def set_device_note(self, client_id: str, alias: str, note: str):
        """Sets custom alias and note for a device and persists to disk."""
        now = time.time()
        alias_clean = alias.strip()
        note_clean = note.strip()
        
        meta = self.device_notes.get(client_id, {})
        meta["alias"] = alias_clean
        meta["note"] = note_clean
        meta["updated_at"] = now
        
        if client_id in self.clients:
            c = self.clients[client_id]
            meta["hostname"] = c.get("hostname", meta.get("hostname", client_id))
            meta["username"] = c.get("username", meta.get("username", ""))
            meta["ip_address"] = c.get("ip_address", meta.get("ip_address", "-"))
            meta["os_name"] = c.get("os_name", meta.get("os_name", "Unknown"))
            meta["os_type"] = c.get("os_type", meta.get("os_type", "unknown"))
            c["alias"] = alias_clean
            c["note"] = note_clean
        else:
            self.clients[client_id] = {
                "device_id": client_id,
                "alias": alias_clean,
                "note": note_clean,
                "hostname": meta.get("hostname", alias_clean or client_id),
                "username": meta.get("username", ""),
                "os_name": meta.get("os_name", "Offline Device"),
                "os_type": meta.get("os_type", "unknown"),
                "os_full": "",
                "ip_address": meta.get("ip_address", "-"),
                "status": "offline",
                "last_seen": meta.get("last_seen", 0),
                "connected_at": 0,
                "metrics": {},
                "thumbnail": "",
                "monitors": []
            }

        self.device_notes[client_id] = meta
        save_device_notes(self.device_notes)
        return self.clients[client_id]

    def update_telemetry(self, client_id: str, metrics: dict, thumbnail: str = None):
        """Updates client metrics and pushes update to admin dashboards."""
        if client_id in self.clients:
            self.clients[client_id]["last_seen"] = time.time()
            self.clients[client_id]["status"] = "in_session" if self.has_active_viewers(client_id) else "online"
            self.clients[client_id]["metrics"] = metrics
            if thumbnail:
                self.clients[client_id]["thumbnail"] = thumbnail
            
            # Update IP and hostname if they changed
            if "ip_address" in metrics:
                self.clients[client_id]["ip_address"] = metrics["ip_address"]
            if "hostname" in metrics:
                self.clients[client_id]["hostname"] = metrics["hostname"]

    def disconnect_client(self, client_id: str):
        """Marks client as offline when its WebSocket disconnects."""
        if client_id in self.client_sockets:
            del self.client_sockets[client_id]
        if client_id in self.clients:
            self.clients[client_id]["status"] = "offline"
            self.clients[client_id]["last_seen"] = time.time()

    def get_all_clients(self):
        """Returns sorted list of clients (online first)."""
        now = time.time()
        
        # Ensure any known device with alias/notes is included even if server restarted
        for cid, meta in self.device_notes.items():
            if cid not in self.clients:
                self.clients[cid] = {
                    "device_id": cid,
                    "alias": meta.get("alias", ""),
                    "note": meta.get("note", ""),
                    "hostname": meta.get("hostname") or meta.get("alias") or cid,
                    "username": meta.get("username", ""),
                    "os_name": meta.get("os_name", "Unknown"),
                    "os_type": meta.get("os_type", "unknown"),
                    "os_full": "",
                    "ip_address": meta.get("ip_address", "-"),
                    "status": "offline",
                    "last_seen": meta.get("last_seen", 0),
                    "connected_at": 0,
                    "metrics": {},
                    "thumbnail": "",
                    "monitors": []
                }

        client_list = []
        for cid, c in self.clients.items():
            # If haven't heard from client in 8 seconds and socket closed, ensure marked offline
            if cid not in self.client_sockets and now - c.get("last_seen", 0) > 8:
                c["status"] = "offline"
            if cid in self.device_notes:
                c["alias"] = self.device_notes[cid].get("alias", "")
                c["note"] = self.device_notes[cid].get("note", "")
            client_list.append(c)
        
        # Sort: online first, then by alias/hostname
        client_list.sort(key=lambda x: (
            0 if x["status"] in ["online", "in_session"] else 1,
            (x.get("alias") or x.get("hostname") or "").lower()
        ))
        return client_list

    # --- Admin Dashboard WebSockets ---
    def register_admin(self, ws: WebSocket):
        self.admin_dashboard_sockets.add(ws)

    def unregister_admin(self, ws: WebSocket):
        self.admin_dashboard_sockets.discard(ws)

    async def broadcast_to_admins(self, message: dict):
        """Broadcasts a JSON message to all connected admin dashboards."""
        if not self.admin_dashboard_sockets:
            return
        dead = set()
        msg_str = json.dumps(message)
        for ws in list(self.admin_dashboard_sockets):
            try:
                await ws.send_text(msg_str)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.admin_dashboard_sockets.discard(ws)

    # --- Remote Viewer WebSockets ---
    def has_active_viewers(self, client_id: str) -> bool:
        viewers = self.remote_viewers.get(client_id)
        return bool(viewers and len(viewers) > 0)

    async def add_remote_viewer(self, client_id: str, ws: WebSocket):
        # Ensure this viewer websocket is removed from any previous client session
        for other_cid in list(self.remote_viewers.keys()):
            if other_cid != client_id and ws in self.remote_viewers[other_cid]:
                await self.remove_remote_viewer(other_cid, ws)

        if client_id not in self.remote_viewers:
            self.remote_viewers[client_id] = set()

        # Purge closed/dead sockets from set
        active = set()
        for v_ws in self.remote_viewers[client_id]:
            try:
                if getattr(v_ws, "client_state", None) and v_ws.client_state.name == "CONNECTED":
                    active.add(v_ws)
            except Exception:
                pass
        self.remote_viewers[client_id] = active
        self.remote_viewers[client_id].add(ws)

        if client_id in self.clients:
            self.clients[client_id]["status"] = "in_session"

        # ALWAYS ensure the target client starts screen streaming
        await self.send_to_client(client_id, {
            "type": "start_stream",
            "scale": 0.75,
            "quality": 60,
            "fps": 22,
            "monitor": 1
        })

    async def remove_remote_viewer(self, client_id: str, ws: WebSocket):
        if client_id in self.remote_viewers:
            self.remote_viewers[client_id].discard(ws)
            # Filter active sockets
            active = set()
            for v_ws in self.remote_viewers[client_id]:
                try:
                    if getattr(v_ws, "client_state", None) and v_ws.client_state.name == "CONNECTED":
                        active.add(v_ws)
                except Exception:
                    pass
            self.remote_viewers[client_id] = active

            if len(self.remote_viewers[client_id]) == 0:
                self.remote_viewers.pop(client_id, None)
                if client_id in self.clients:
                    self.clients[client_id]["status"] = "online"
                # Stop streaming on client to conserve resources
                await self.send_to_client(client_id, {"type": "stop_stream"})

    async def forward_frame_to_viewers(self, client_id: str, frame_data: dict):
        """Relays a captured screen frame to all admin viewers for this client."""
        viewers = self.remote_viewers.get(client_id)
        if not viewers:
            return
        dead = set()
        msg_str = json.dumps(frame_data)
        for ws in list(viewers):
            try:
                await ws.send_text(msg_str)
            except Exception:
                dead.add(ws)
        for ws in dead:
            viewers.discard(ws)

    # --- Communication with Client ---
    async def send_to_client(self, client_id: str, message: dict):
        ws = self.client_sockets.get(client_id)
        if ws:
            try:
                await ws.send_text(json.dumps(message))
                return True
            except Exception:
                return False
        return False

    async def send_request_to_client(self, client_id: str, message: dict, timeout=10.0):
        """Sends a request to client and awaits response via future."""
        req_id = message.get("req_id")
        if not req_id:
            return None
            
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self.pending_requests[req_id] = future

        sent = await self.send_to_client(client_id, message)
        if not sent:
            self.pending_requests.pop(req_id, None)
            return {"success": False, "error": "Client not connected"}

        try:
            res = await asyncio.wait_for(future, timeout=timeout)
            return res
        except asyncio.TimeoutError:
            return {"success": False, "error": "Request timed out"}
        finally:
            self.pending_requests.pop(req_id, None)

    def resolve_pending_request(self, req_id: str, data: Any):
        """Resolves an awaiting request future."""
        future = self.pending_requests.get(req_id)
        if future and not future.done():
            future.set_result(data)

client_manager = ClientManager()
