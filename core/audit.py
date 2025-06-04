import os
import threading
import logging
from datetime import datetime

AUDIT_LOG_PATH = "db/audit.log"
_log_lock = threading.Lock()

def audit_log(user_id: str, module: str, action: str, status: str, details: str = ""):
    """
    Append a single line to db/audit.log in the format:
      TIMESTAMP | user_id | module | action | status | details
    """
    timestamp = datetime.utcnow().isoformat()
    line = f"{timestamp} | {user_id} | {module} | {action} | {status} | {details}\n"
    with _log_lock:
        with open(AUDIT_LOG_PATH, "a") as f:
            f.write(line)

def get_recent_logs(n: int = 100) -> list:
    """
    Return the last n lines of audit.log as a list of strings.
    """
    if not os.path.exists(AUDIT_LOG_PATH):
        return []
    with open(AUDIT_LOG_PATH, "r") as f:
        lines = f.readlines()
    return lines[-n:]
