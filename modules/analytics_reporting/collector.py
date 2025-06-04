import asyncio
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
import logging
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from core.database import (
    get_db, User, Session as DBSession, Message, 
    Memory, AuditLog, Project, Plugin
)
from core.config import settings
from .utils import is_cache_valid, cache_metrics
from .system import SystemMetrics
from .user import UserAnalytics  
from .chat import ChatAnalytics
from .reports import ReportGenerator

logger = logging.getLogger(__name__)

class AnalyticsCollector:
    """Collects and aggregates analytics data. (Features: 29, 31, 55, 66, 76, 78, 80, 81, 120, 122, 123, 124, 129, 133, 134, 135, 136, 201, 202, 203)"""
    
    def __init__(self, db: Session):
        self.db = db
        self.metrics_cache = {}
        self.cache_timeout = 300  # 5 minutes
        self.system_metrics = SystemMetrics(db)
        self.user_analytics = UserAnalytics(db)
        self.chat_analytics = ChatAnalytics(db)
        self.report_generator = ReportGenerator(db)
        
    async def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect overall system metrics. (Features: 29, 31, 120, 122, 123, 124, 134, 135, 136)"""
        cache_key = "system_metrics"
        if is_cache_valid(self.metrics_cache, cache_key, self.cache_timeout):
            return self.metrics_cache[cache_key]["data"]
        
        try:
            metrics = await self.system_metrics.collect_all()
            cache_metrics(self.metrics_cache, cache_key, metrics)
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {}
    
    async def collect_user_analytics(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Collect analytics for a specific user. (Features: 29, 31, 66, 76, 78, 80, 81, 134, 201, 202, 203)"""
        try:
            return await self.user_analytics.collect_for_user(user_id, days)
        except Exception as e:
            logger.error(f"Error collecting user analytics for {user_id}: {e}")
            return {}
    
    async def collect_chat_analytics(self, session_id: int) -> Dict[str, Any]:
        """Collect analytics for a specific chat session. (Features: 29, 31, 66, 76, 78, 80, 81, 134, 201, 202, 203)"""
        try:
            return await self.chat_analytics.collect_for_session(session_id)
        except Exception as e:
            logger.error(f"Error collecting chat analytics for session {session_id}: {e}")
            return {}
    
    async def generate_report(
        self, 
        report_type: str, 
        start_date: datetime, 
        end_date: datetime,
        filters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Generate various types of analytics reports. (Features: 29, 31, 55, 111, 120, 122, 123, 124, 134, 135, 136)"""
        try:
            return await self.report_generator.generate(report_type, start_date, end_date, filters)
        except Exception as e:
            logger.error(f"Error generating {report_type} report: {e}")
            return {"error": str(e)}

def get_analytics_collector(db: Session) -> AnalyticsCollector:
    """Get analytics collector instance. (Features: 29, 31, 134)"""
    return AnalyticsCollector(db) 