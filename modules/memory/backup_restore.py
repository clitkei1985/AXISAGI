# modules/memory/backup_restore.py

import os
import shutil
import logging
from datetime import datetime
from core.config import Config
from core.security import encrypt_data, decrypt_data, compute_checksum, verify_checksum
from core.audit import audit_log

logger = logging.getLogger("axis.memory.backup_restore")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler(Config.LOG_PATH)
fh.setFormatter(logging.Formatter("%(asctime)s | MEMORY_BACKUP | %(levelname)s | %(message)s"))
logger.addHandler(fh)

class BackupRestore:
    @staticmethod
    def backup_now():
        """
        Create an encrypted backup of every session’s FAISS + pickle files under db/backups/{timestamp}/
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        dest_root = os.path.join(os.getcwd(), Config.BACKUP_PATH, timestamp)
        os.makedirs(dest_root, exist_ok=True)

        # Look for any files matching memory_{session_id}.faiss / .pkl
        base_dir = os.path.dirname(Config.MEMORY_PATH) or "db"
        for fname in os.listdir(base_dir):
            if fname.startswith("memory_") and (fname.endswith(".faiss") or fname.endswith(".pkl")):
                src = os.path.join(base_dir, fname)
                try:
                    with open(src, "rb") as f:
                        data = f.read()
                    token = encrypt_data(data)
                    out_name = fname + ".enc"
                    out_path = os.path.join(dest_root, out_name)
                    with open(out_path, "wb") as outf:
                        outf.write(token)
                    checksum = compute_checksum(out_path)
                    with open(out_path + ".sha256", "w") as cf:
                        cf.write(checksum)
                    audit_log(user_id="system", module="memory_backup", action="backup", status="OK", details=out_name)
                    logger.info(f"Backed up {src} → {out_path}")
                except Exception as e:
                    audit_log(user_id="system", module="memory_backup", action="backup", status="ERROR", details=str(e))
                    logger.exception(f"Error backing up {src}: {e}")

    @staticmethod
    def list_backups() -> list:
        """
        Return a sorted list of timestamps (directory names) under backups/.
        """
        backup_root = os.path.join(os.getcwd(), Config.BACKUP_PATH)
        if not os.path.isdir(backup_root):
            return []
        dirs = [d for d in os.listdir(backup_root) if os.path.isdir(os.path.join(backup_root, d))]
        return sorted(dirs)

    @staticmethod
    def restore(timestamp: str):
        """
        Given a timestamp folder under db/backups, decrypt each .enc file and overwrite the FAISS/.pkl.
        """
        backup_dir = os.path.join(os.getcwd(), Config.BACKUP_PATH, timestamp)
        if not os.path.isdir(backup_dir):
            raise FileNotFoundError(f"Backup '{timestamp}' not found.")

        for fname in os.listdir(backup_dir):
            if fname.endswith(".faiss.enc") or fname.endswith(".pkl.enc"):
                enc_path = os.path.join(backup_dir, fname)
                try:
                    # Verify checksum
                    checksum_file = enc_path + ".sha256"
                    if not verify_checksum(enc_path, checksum_file):
                        logger.warning(f"Checksum mismatch for {enc_path}. Skipping restore.")
                        audit_log(user_id="system", module="memory_restore", action="restore", status="CHECKSUM_FAIL", details=fname)
                        continue

                    with open(enc_path, "rb") as f:
                        token = f.read()
                    data = decrypt_data(token)
                    # Write to original location: strip trailing ".enc"
                    orig_name = fname[:-4]
                    base_dir = os.path.dirname(Config.MEMORY_PATH) or "db"
                    out_path = os.path.join(base_dir, orig_name)
                    with open(out_path, "wb") as outf:
                        outf.write(data)
                    audit_log(user_id="system", module="memory_restore", action="restore", status="OK", details=orig_name)
                    logger.info(f"Restored {out_path} from {enc_path}.")
                except Exception as e:
                    audit_log(user_id="system", module="memory_restore", action="restore", status="ERROR", details=str(e))
                    logger.exception(f"Error restoring {enc_path}: {e}")
