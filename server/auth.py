import os
import json
import secrets
import hashlib
import time
from typing import Optional, Dict

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

# In-memory active tokens: token -> {"created_at": float, "expires_at": float, "remember": bool}
ACTIVE_SESSIONS: Dict[str, dict] = {}

DEFAULT_CONFIG = {
    "password_hash": "",
    "password_salt": "",
    "server_name": "LAN Remote Desktop Server",
    "session_timeout_hours": 24,
    "remember_days": 30,
    "require_login": True,
    "setup_completed": False
}

def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                cfg = DEFAULT_CONFIG.copy()
                cfg.update(data)
                return cfg
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(cfg: dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4)

def hash_password(password: str, salt: Optional[bytes] = None) -> (str, str):
    """Hashes password with PBKDF2-HMAC-SHA256 (100,000 iterations)."""
    if salt is None:
        salt = secrets.token_bytes(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return hashed.hex(), salt.hex()

def is_setup_completed() -> bool:
    cfg = load_config()
    return bool(cfg.get("setup_completed") and cfg.get("password_hash"))

def verify_password(password: str) -> bool:
    cfg = load_config()
    if not cfg.get("password_hash") or not cfg.get("password_salt"):
        return False
    salt = bytes.fromhex(cfg["password_salt"])
    expected_hash = cfg["password_hash"]
    test_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(expected_hash, test_hash)

def set_admin_password(password: str) -> bool:
    if not password or len(password) < 4:
        return False
    cfg = load_config()
    hashed, salt = hash_password(password)
    cfg["password_hash"] = hashed
    cfg["password_salt"] = salt
    cfg["setup_completed"] = True
    save_config(cfg)
    return True

def create_session_token(remember_me: bool = False) -> str:
    cfg = load_config()
    token = secrets.token_hex(32)
    now = time.time()
    
    if remember_me:
        days = cfg.get("remember_days", 30)
        duration = days * 86400
    else:
        hours = cfg.get("session_timeout_hours", 24)
        duration = hours * 3600
        
    ACTIVE_SESSIONS[token] = {
        "created_at": now,
        "expires_at": now + duration,
        "remember": remember_me
    }
    return token

def verify_token(token: Optional[str]) -> bool:
    if not token:
        return False
    session = ACTIVE_SESSIONS.get(token)
    if not session:
        return False
    if time.time() > session["expires_at"]:
        ACTIVE_SESSIONS.pop(token, None)
        return False
    return True

def revoke_token(token: str):
    ACTIVE_SESSIONS.pop(token, None)
