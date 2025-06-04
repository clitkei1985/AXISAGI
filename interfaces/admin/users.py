from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import secrets
import logging

from core.database import get_db, User, Session as DBSession, Message, Memory, AuditLog
from core.security import get_current_admin_user, get_password_hash
from .schemas import (
    UserInfo,
    UserCreate,
    UserUpdate,
    BulkUserAction,
    AdminActionResult,
    PaginatedResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=PaginatedResponse)
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_admin: Optional[bool] = None,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List all users with filtering and pagination."""
    try:
        query = db.query(User)
        
        # Apply filters
        if search:
            query = query.filter(
                (User.username.ilike(f"%{search}%")) |
                (User.email.ilike(f"%{search}%"))
            )
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        if is_admin is not None:
            query = query.filter(User.is_admin == is_admin)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        users = query.offset(offset).limit(per_page).all()
        
        # Convert to UserInfo objects
        user_infos = []
        for user in users:
            # Get user statistics
            session_count = db.query(DBSession).filter(DBSession.user_id == user.id).count()
            message_count = db.query(Message).join(DBSession).filter(DBSession.user_id == user.id).count()
            
            user_infos.append(UserInfo(
                id=user.id,
                username=user.username,
                email=user.email,
                is_active=user.is_active,
                is_admin=user.is_admin,
                created_at=user.created_at,
                last_login=user.last_login,
                session_count=session_count,
                total_messages=message_count,
                storage_used_mb=0.0  # Would calculate actual storage usage
            ))
        
        return PaginatedResponse(
            items=user_infos,
            total=total,
            page=page,
            per_page=per_page,
            pages=(total + per_page - 1) // per_page
        )
        
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail="Failed to list users")

@router.post("/", response_model=UserInfo)
async def create_user(
    user_data: UserCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new user."""
    try:
        # Check if username or email already exists
        existing_user = db.query(User).filter(
            (User.username == user_data.username) | (User.email == user_data.email)
        ).first()
        
        if existing_user:
            raise HTTPException(status_code=400, detail="Username or email already exists")
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            is_active=True,
            is_admin=user_data.is_admin,
            created_at=datetime.utcnow()
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Log the action
        audit_entry = AuditLog(
            user_id=current_admin.id,
            action="create_user",
            resource_type="user",
            resource_id=str(new_user.id),
            details={"username": user_data.username, "email": user_data.email},
            ip_address="127.0.0.1",
            timestamp=datetime.utcnow()
        )
        db.add(audit_entry)
        db.commit()
        
        return UserInfo(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email,
            is_active=new_user.is_active,
            is_admin=new_user.is_admin,
            created_at=new_user.created_at,
            last_login=None,
            session_count=0,
            total_messages=0,
            storage_used_mb=0.0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user")

@router.put("/{user_id}", response_model=UserInfo)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update a user."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update fields
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        db.commit()
        db.refresh(user)
        
        # Log the action
        audit_entry = AuditLog(
            user_id=current_admin.id,
            action="update_user",
            resource_type="user",
            resource_id=str(user_id),
            details=update_data,
            ip_address="127.0.0.1",
            timestamp=datetime.utcnow()
        )
        db.add(audit_entry)
        db.commit()
        
        # Get updated user info
        session_count = db.query(DBSession).filter(DBSession.user_id == user.id).count()
        message_count = db.query(Message).join(DBSession).filter(DBSession.user_id == user.id).count()
        
        return UserInfo(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            is_admin=user.is_admin,
            created_at=user.created_at,
            last_login=user.last_login,
            session_count=session_count,
            total_messages=message_count,
            storage_used_mb=0.0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user")

@router.delete("/{user_id}", response_model=AdminActionResult)
async def delete_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Delete a user and all associated data."""
    try:
        if user_id == current_admin.id:
            raise HTTPException(status_code=400, detail="Cannot delete yourself")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Delete associated data
        # Sessions and messages will be cascade deleted
        db.query(Memory).filter(Memory.user_id == user_id).delete()
        db.delete(user)
        db.commit()
        
        # Log the action
        audit_entry = AuditLog(
            user_id=current_admin.id,
            action="delete_user",
            resource_type="user",
            resource_id=str(user_id),
            details={"username": user.username},
            ip_address="127.0.0.1",
            timestamp=datetime.utcnow()
        )
        db.add(audit_entry)
        db.commit()
        
        return AdminActionResult(
            success=True,
            message=f"User {user.username} deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete user")

@router.post("/bulk-action", response_model=AdminActionResult)
async def bulk_user_action(
    action_request: BulkUserAction,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Perform bulk actions on multiple users."""
    try:
        users = db.query(User).filter(User.id.in_(action_request.user_ids)).all()
        if not users:
            raise HTTPException(status_code=404, detail="No users found")
        
        affected_count = 0
        
        if action_request.action == "activate":
            for user in users:
                user.is_active = True
                affected_count += 1
        
        elif action_request.action == "deactivate":
            for user in users:
                if user.id != current_admin.id:  # Don't deactivate self
                    user.is_active = False
                    affected_count += 1
        
        elif action_request.action == "delete":
            for user in users:
                if user.id != current_admin.id:  # Don't delete self
                    db.query(Memory).filter(Memory.user_id == user.id).delete()
                    db.delete(user)
                    affected_count += 1
        
        elif action_request.action == "reset_password":
            for user in users:
                # Generate temporary password
                temp_password = secrets.token_urlsafe(12)
                user.hashed_password = get_password_hash(temp_password)
                affected_count += 1
                # In real implementation, would send email with temp password
        
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
        
        db.commit()
        
        # Log the action
        audit_entry = AuditLog(
            user_id=current_admin.id,
            action=f"bulk_{action_request.action}",
            resource_type="user",
            details={"user_ids": action_request.user_ids, "reason": action_request.reason},
            ip_address="127.0.0.1",
            timestamp=datetime.utcnow()
        )
        db.add(audit_entry)
        db.commit()
        
        return AdminActionResult(
            success=True,
            message=f"Bulk action '{action_request.action}' completed",
            affected_count=affected_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing bulk action: {e}")
        raise HTTPException(status_code=500, detail="Failed to perform bulk action") 