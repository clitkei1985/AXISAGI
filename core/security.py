from .security.auth import *
from .security.roles import *
from .security.encryption import *
from .security.checksum import *
from .security.backup import *
from .security.logger import *

import os
import logging
import hashlib
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from core.config import settings
from core.database import get_db, User
import secrets

logger = logging.getLogger("axis.security")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler("db/audit.log")
fh.setFormatter(logging.Formatter("%(asctime)s | SECURITY | %(levelname)s | %(message)s"))
logger.addHandler(fh)

# You may set AXIS_ENCRYPTION_KEY in env for persistence; otherwise generate a new one each run.
FERNET_KEY = os.environ.get("AXIS_ENCRYPTION_KEY") or Fernet.generate_key()
_f = Fernet(FERNET_KEY)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.security.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.security.secret_key, 
        algorithm=settings.security.algorithm
    )
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.security.refresh_token_expire_days)
    to_encode.update({"exp": expire, "refresh": True})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.security.secret_key,
        algorithm=settings.security.algorithm
    )
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token,
            settings.security.secret_key,
            algorithms=[settings.security.algorithm]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current admin user."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

def validate_password(password: str) -> bool:
    """
    Validate password strength.
    Returns True if password meets requirements, False otherwise.
    """
    if len(password) < settings.security.password_min_length:
        return False
    
    # Check for at least one number
    if not any(char.isdigit() for char in password):
        return False
    
    # Check for at least one uppercase letter
    if not any(char.isupper() for char in password):
        return False
    
    # Check for at least one lowercase letter
    if not any(char.islower() for char in password):
        return False
    
    # Check for at least one special character
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(char in special_chars for char in password):
        return False
    
    return True

def generate_secret_key() -> str:
    """Generate a secure random secret key."""
    return secrets.token_urlsafe(32)

def encrypt_sensitive_data(data: str) -> str:
    """Encrypt sensitive data using the configured encryption key."""
    # Implementation depends on chosen encryption method
    # This is a placeholder for actual encryption logic
    return data

def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Decrypt sensitive data using the configured encryption key."""
    # Implementation depends on chosen encryption method
    # This is a placeholder for actual decryption logic
    return encrypted_data

# Role-based access control
class RoleChecker:
    def __init__(self, required_roles: list):
        self.required_roles = required_roles
    
    def __call__(self, user: User = Depends(get_current_active_user)):
        for role in self.required_roles:
            if not hasattr(user, role) or not getattr(user, role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role {role} required"
                )
        return user

# Usage example:
# require_admin = RoleChecker(["is_admin"])
# @app.get("/admin", dependencies=[Depends(require_admin)])

def encrypt_data(data: bytes) -> bytes:
    """
    Encrypt bytes using Fernet. Returns token.
    """
    try:
        token = _f.encrypt(data)
        logger.debug(f"Data encrypted ({len(data)} bytes → {len(token)} bytes).")
        return token
    except Exception as e:
        logger.exception(f"Error encrypting data: {e}")
        raise

def decrypt_data(token: bytes) -> bytes:
    """
    Decrypt Fernet token back into plaintext bytes.
    """
    try:
        plaintext = _f.decrypt(token)
        logger.debug(f"Data decrypted ({len(token)} bytes → {len(plaintext)} bytes).")
        return plaintext
    except Exception as e:
        logger.exception(f"Error decrypting data: {e}")
        raise

def compute_checksum(filepath: str) -> str:
    """
    Compute SHA‐256 checksum of a file.
    """
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
    """
    Verify the SHA256 checksum stored in checksum_file matches computed checksum.
    """
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

def backup_memory_index():
    """
    Create an encrypted backup of memory index files (e.g. memory_index.faiss & memory_index.pkl),
    store under BACKUP_PATH with timestamp folder.
    """
    from datetime import datetime
    base = os.getcwd()
    mem_faiss = Config.MEMORY_PATH + ".faiss"
    mem_pkl = Config.MEMORY_PATH + ".pkl"
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    dest_dir = os.path.join(os.getcwd(), Config.BACKUP_PATH, timestamp)
    os.makedirs(dest_dir, exist_ok=True)

    for path in (mem_faiss, mem_pkl):
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    data = f.read()
                token = encrypt_data(data)
                filename = os.path.basename(path) + ".enc"
                out_path = os.path.join(dest_dir, filename)
                with open(out_path, "wb") as outf:
                    outf.write(token)
                logger.info(f"Backed up and encrypted {path} → {out_path}")
                # Write checksum
                checksum = hashlib.sha256(token).hexdigest()
                with open(out_path + ".sha256", "w") as cf:
                    cf.write(checksum)
            except Exception as e:
                logger.exception(f"Failed to backup {path}: {e}")
        else:
            logger.warning(f"Memory index file not found for backup: {path}")
