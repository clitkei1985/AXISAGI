from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import logging

from core.database import get_db, User
from core.security import get_current_active_user
from modules.analytics_reporting.analytics import get_analytics_collector
from .schemas import SystemMetrics, UserAnalytics, ChatAnalytics

logger = logging.getLogger(__name__)
metrics_router = APIRouter()

@metrics_router.get("/metrics/system", response_model=SystemMetrics)
async def get_system_metrics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    collector = get_analytics_collector(db)
    metrics = await collector.collect_system_metrics()
    if not metrics:
        raise HTTPException(status_code=500, detail="Failed to collect system metrics")
    return SystemMetrics(**metrics)

@metrics_router.get("/metrics/user/{user_id}", response_model=UserAnalytics)
async def get_user_analytics(
    user_id: int,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    collector = get_analytics_collector(db)
    analytics = await collector.collect_user_analytics(user_id, days)
    if not analytics:
        raise HTTPException(status_code=404, detail="User not found or no data available")
    return UserAnalytics(**analytics)

@metrics_router.get("/metrics/chat/{session_id}", response_model=ChatAnalytics)
async def get_chat_analytics(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    from core.database import Session as DBSession
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    collector = get_analytics_collector(db)
    analytics = await collector.collect_chat_analytics(session_id)
    if not analytics:
        raise HTTPException(status_code=500, detail="Failed to collect chat analytics")
    return ChatAnalytics(**analytics)

@metrics_router.get("/realtime/metrics")
async def get_realtime_metrics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    collector = get_analytics_collector(db)
    metrics = await collector.collect_realtime_metrics()
    if not metrics:
        raise HTTPException(status_code=500, detail="Failed to collect realtime metrics")
    return metrics 