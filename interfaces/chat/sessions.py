from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from core.database import get_db, Session as DBSession, User
from core.security import get_current_active_user
from .schemas import ChatSession, SessionCreate, SessionUpdate

sessions_router = APIRouter()

@sessions_router.post("/sessions/", response_model=ChatSession)
async def create_session(
    session: SessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new chat session. (Features: 2, 37, 43, 45, 121, 127, 201, 202, 203)"""
    db_session = DBSession(
        user_id=current_user.id,
        session_type="chat",
        extra_metadata={
            **session.metadata,
            "created_by": current_user.username,
            "model_config": session.model_config_data
        }
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

@sessions_router.get("/sessions/", response_model=List[ChatSession])
async def list_sessions(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all chat sessions for the current user. (Features: 2, 37, 43, 44, 45, 121, 127)"""
    return db.query(DBSession).filter(
        DBSession.user_id == current_user.id,
        DBSession.session_type == "chat"
    ).order_by(DBSession.start_time.desc()).offset(skip).limit(limit).all()

@sessions_router.get("/sessions/{session_id}", response_model=ChatSession)
async def get_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific chat session. (Features: 2, 37, 43, 45, 121, 127)"""
    session = db.query(DBSession).filter(
        DBSession.id == session_id,
        DBSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@sessions_router.put("/sessions/{session_id}", response_model=ChatSession)
async def update_session(
    session_id: int,
    session_update: SessionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a chat session. (Features: 2, 37, 43, 45, 121, 127)"""
    session = db.query(DBSession).filter(
        DBSession.id == session_id,
        DBSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Handle field mapping for session updates
    update_data = session_update.dict(exclude_unset=True)
    if 'metadata' in update_data:
        session.extra_metadata.update(update_data.pop('metadata'))
    
    for key, value in update_data.items():
        setattr(session, key, value)
    
    db.commit()
    db.refresh(session)
    return session

@sessions_router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a chat session. (Features: 2, 37, 43, 45, 121, 127)"""
    session = db.query(DBSession).filter(
        DBSession.id == session_id,
        DBSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()
    return {"detail": "Session deleted"} 