import hashlib
import logging

logger = logging.getLogger("axis.security.checksum")

def compute_checksum(filepath: str) -> str:
    sha256 = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        checksum = sha256.hexdigest()
        logger.debug(f"Computed checksum for {filepath}: {checksum}")
        return checksum
    except Exception as e:
        logger.exception(f"Error computing checksum for {filepath}: {e}")
        raise

def verify_checksum(filepath: str, checksum_file: str) -> bool:
    try:
        computed = compute_checksum(filepath)
        with open(checksum_file, "r") as f:
            stored = f.read().strip()
        if computed == stored:
            logger.debug(f"Checksum match for {filepath}.")
            return True
        else:
            logger.warning(f"Checksum mismatch for {filepath}: computed {computed}, stored {stored}")
            return False
    except Exception as e:
        logger.exception(f"Error verifying checksum: {e}")
        return False 