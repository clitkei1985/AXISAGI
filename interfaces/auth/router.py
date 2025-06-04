from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from typing import Dict
from jose import JWTError, jwt

from core.database import get_db, User
from core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    get_password_hash,
    validate_password,
    get_current_active_user
)
from core.config import settings
from .schemas import UserCreate, Token, UserResponse

router = APIRouter()

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Authenticate user and return tokens."""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    return {
        "access_token": create_access_token(data={"sub": user.username}),
        "refresh_token": create_refresh_token(data={"sub": user.username}),
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Get new access token using refresh token."""
    try:
        payload = jwt.decode(
            current_token,
            settings.security.secret_key,
            algorithms=[settings.security.algorithm]
        )
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        if not payload.get("refresh"):
            raise HTTPException(status_code=401, detail="Not a refresh token")
            
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
            
        return {
            "access_token": create_access_token(data={"sub": username}),
            "refresh_token": create_refresh_token(data={"sub": username}),
            "token_type": "bearer"
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user."""
    # Check if username exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate password strength
    if not validate_password(user_data.password):
        raise HTTPException(
            status_code=400,
            detail="Password does not meet security requirements"
        )
    
    # Create user
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        is_active=True,
        is_admin=False
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        is_active=user.is_active,
        is_admin=user.is_admin,
        created_at=user.created_at
    )

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user)
):
    """Logout user (client should discard tokens)."""
    return {"detail": "Successfully logged out"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information."""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        is_active=current_user.is_active,
        is_admin=current_user.is_admin,
        created_at=current_user.created_at
    ) 