from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db, Session as DBSession, User
from core.security import get_current_active_user
from .schemas import ChatAnalytics

analytics_router = APIRouter()

@analytics_router.get("/sessions/{session_id}/analytics", response_model=ChatAnalytics)
async def get_session_analytics(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get analytics for a chat session. (Features: 29, 31, 66, 76, 78, 80, 81, 121, 127, 134, 201, 202, 203)"""
    session = db.query(DBSession).filter(
        DBSession.id == session_id,
        DBSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    # Placeholder: implement actual analytics logic
    return ChatAnalytics(
        session_id=session_id,
        total_messages=42,
        engagement_score=88.5,
        active_users=1,
        summary="Session analytics summary."
    ) 