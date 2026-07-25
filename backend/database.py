import json
import os
import hashlib
import hmac
import base64
import tempfile
import time
import glob as glob_mod
import platform
from datetime import datetime

# --- Data Directory ---
def get_data_dir():
    try:
        from android.storage import app_storage_path
        base = app_storage_path()
    except Exception:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    d = os.path.join(base, "data")
    os.makedirs(d, exist_ok=True)
    return d

DATA_DIR = get_data_dir()

def json_path(name):
    return os.path.join(DATA_DIR, f"{name}.json")

# --- Encryption Key ---
_KEY_FILE = os.path.join(get_data_dir(), ".secret_key")

def _get_encryption_key():
    if os.path.exists(_KEY_FILE):
        with open(_KEY_FILE, "rb") as f:
            return f.read()
    key = os.urandom(32)
    with open(_KEY_FILE, "wb") as f:
        f.write(key)
    return key

def _xor_encrypt(data, key):
    key_len = len(key)
    return bytes(b ^ key[i % key_len] for i, b in enumerate(data))

def _encrypt_str(text):
    key = _get_encryption_key()
    raw = text.encode("utf-8")
    encrypted = _xor_encrypt(raw, key)
    return base64.b64encode(encrypted).decode("ascii")

def _decrypt_str(b64_text):
    key = _get_encryption_key()
    encrypted = base64.b64decode(b64_text)
    decrypted = _xor_encrypt(encrypted, key)
    return decrypted.decode("utf-8")

# --- File Locking ---
import threading
_file_locks = {}
_global_lock = threading.Lock()

def _get_lock(path):
    with _global_lock:
        if path not in _file_locks:
            _file_locks[path] = threading.Lock()
        return _file_locks[path]

# --- JSON Load/Save (encrypted + atomic) ---
_SENSITIVE_FILES = {"staff"}

def load_json(name, default=None):
    p = json_path(name)
    lock = _get_lock(p)
    lock.acquire()
    try:
        if os.path.exists(p):
            with open(p, "r") as f:
                content = f.read()
            if name in _SENSITIVE_FILES and content.startswith("ENC:"):
                try:
                    content = _decrypt_str(content[4:])
                except Exception:
                    pass
            return json.loads(content)
        return default if default is not None else {}
    finally:
        lock.release()

def save_json(name, data):
    p = json_path(name)
    lock = _get_lock(p)
    lock.acquire()
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        text = json.dumps(data, indent=2)
        if name in _SENSITIVE_FILES:
            text = "ENC:" + _encrypt_str(text)
        dir_name = os.path.dirname(p)
        fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as f:
                f.write(text)
            os.replace(tmp_path, p)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
    finally:
        lock.release()

def today_key():
    return datetime.now().strftime("%Y-%m-%d")

def time_key():
    return datetime.now().strftime("%H:%M:%S")

# --- Password Hashing (PBKDF2 + salt) ---
def hash_pw(pw):
    salt = os.urandom(16)
    h = hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), salt, 100000)
    return base64.b64encode(salt).decode() + ":" + base64.b64encode(h).decode()

def verify_pw(pw, stored):
    if not stored:
        return False
    if ":" in stored:
        try:
            salt_b64, hash_b64 = stored.split(":", 1)
            salt = base64.b64decode(salt_b64)
            expected = base64.b64decode(hash_b64)
            actual = hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), salt, 100000)
            return hmac.compare_digest(actual, expected)
        except Exception:
            return False
    legacy = hashlib.sha256(pw.encode("utf-8")).hexdigest()
    return hmac.compare_digest(legacy, stored)

def migrate_pw(pw, stored, username):
    if ":" not in stored:
        staff = load_json("staff", {"accounts": {}})
        acc = staff.get("accounts", {}).get(username)
        if acc:
            acc["password_hash"] = hash_pw(pw)
            save_json("staff", staff)

# --- Session Manager ---
class SessionManager:
    TIMEOUT_SECONDS = 600  # 10 minutes

    def __init__(self):
        self._last_activity = time.time()
        self._user = None

    def touch(self):
        self._last_activity = time.time()

    def set_user(self, user_info):
        self._user = user_info
        self.touch()

    def clear_user(self):
        self._user = None

    def get_user(self):
        return self._user

    def is_expired(self):
        return (time.time() - self._last_activity) > self.TIMEOUT_SECONDS

    def is_logged_in(self):
        return self._user is not None and not self.is_expired()

session = SessionManager()

def seed_default_staff():
    staff = load_json("staff", None)
    if staff is None or not staff.get("accounts"):
        save_json("staff", {
            "accounts": {
                "admin": {
                    "password_hash": hash_pw("changeme"),
                    "role": "admin",
                    "display_name": "Admin",
                }
            }
        })
