import os
import json
from pathlib import Path

PROFILE_FILE = str(Path.home() / ".aetherdb_profiles.json")
DEFAULT_PROFILE = {
    "host": "127.0.0.1",
    "user": "aether",
    "port": 5432,
    "database": "aetherdb"
}

def load_profiles():
    if not os.path.exists(PROFILE_FILE):
        return {"default": DEFAULT_PROFILE}
    with open(PROFILE_FILE, "r") as f:
        return json.load(f)

def save_profiles(profiles):
    with open(PROFILE_FILE, "w") as f:
        json.dump(profiles, f, indent=2)

def get_profile(name=None):
    profiles = load_profiles()
    if not name: name = "default"
    return profiles.get(name, DEFAULT_PROFILE)

def list_profile_names():
    return list(load_profiles().keys())
