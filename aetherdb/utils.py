import json
import time
from threading import Lock

_LOG_FILE = "aetherdb_audit.log"
_log_lock = Lock()

def audit_log(user, action, detail=None):
    entry = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "user": user,
        "action": action,
        "detail": detail
    }
    with _log_lock:
        with open(_LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
