import json
import os
import hashlib
import glob as glob_mod
from datetime import datetime

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

def load_json(name, default=None):
    p = json_path(name)
    if os.path.exists(p):
        with open(p, "r") as f:
            return json.load(f)
    return default if default is not None else {}

def save_json(name, data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(json_path(name), "w") as f:
        json.dump(data, f, indent=2)

def today_key():
    return datetime.now().strftime("%Y-%m-%d")

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()
