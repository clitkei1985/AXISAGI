from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db, Session as DBSession, Message, User
from core.security import get_current_active_user
from .metrics import metrics_router
from .reports import reports_router
from .dashboards import dashboards_router
from .export import export_router
from .insights import insights_router

router = APIRouter()

@router.get("/overview")
async def get_overview(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get system overview statistics."""
    try:
        # Basic stats
        total_sessions = db.query(DBSession).count()
        total_messages = db.query(Message).count()
        user_sessions = db.query(DBSession).filter(DBSession.user_id == current_user.id).count()
        user_messages = db.query(Message).join(DBSession).filter(DBSession.user_id == current_user.id).count()
        
        return {
            "sessions": {
                "total": total_sessions,
                "user": user_sessions
            },
            "messages": {
                "total": total_messages,
                "user": user_messages
            },
            "code_files": 0,  # Placeholder
            "plugins": {
                "active": 0  # Placeholder
            },
            "recent_activity": [
                {
                    "description": "Chat session created",
                    "timestamp": "2025-06-03T21:00:00Z"
                }
            ]
        }
    except Exception as e:
        return {
            "sessions": {"total": 0, "user": 0},
            "messages": {"total": 0, "user": 0},
            "code_files": 0,
            "plugins": {"active": 0},
            "recent_activity": []
        }

router.include_router(metrics_router)
router.include_router(reports_router)
router.include_router(dashboards_router)
router.include_router(export_router)
router.include_router(insights_router)
