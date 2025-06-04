import os
import logging
import secrets
from cryptography.fernet import Fernet

logger = logging.getLogger("axis.security.encryption")

FERNET_KEY = os.environ.get("AXIS_ENCRYPTION_KEY") or Fernet.generate_key()
_f = Fernet(FERNET_KEY)

def generate_secret_key() -> str:
    return secrets.token_urlsafe(32)

def encrypt_data(data: bytes) -> bytes:
    try:
        token = _f.encrypt(data)
        logger.debug(f"Data encrypted ({len(data)} bytes → {len(token)} bytes).")
        return token
    except Exception as e:
        logger.exception(f"Error encrypting data: {e}")
        raise

def decrypt_data(token: bytes) -> bytes:
    try:
        plaintext = _f.decrypt(token)
        logger.debug(f"Data decrypted ({len(token)} bytes → {len(plaintext)} bytes).")
        return plaintext
    except Exception as e:
        logger.exception(f"Error decrypting data: {e}")
        raise

def encrypt_sensitive_data(data: str) -> str:
    # Placeholder for actual encryption logic
    return data

def decrypt_sensitive_data(encrypted_data: str) -> str:
    # Placeholder for actual decryption logic
    return encrypted_data 