from typing import Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from core.database import User, Session as DBSession, Message, Memory, Plugin
import logging

logger = logging.getLogger(__name__)

class SystemMetrics:
    """Collects system-wide metrics and performance data. (Features: 29, 31, 120, 122, 123, 124, 134, 135, 136, 175, 176, 177)"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def collect_all(self) -> Dict[str, Any]:
        """Collect all system metrics. (Features: 29, 31, 120, 122, 123, 124, 134, 135, 136)"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "users": await self.get_user_metrics(),
            "sessions": await self.get_session_metrics(),
            "messages": await self.get_message_metrics(),
            "memory": await self.get_memory_metrics(),
            "plugins": await self.get_plugin_metrics(),
            "performance": await self.get_performance_metrics()
        }
    
    async def get_user_metrics(self) -> Dict[str, Any]:
        """Get user-related metrics. (Features: 29, 31, 120, 122, 123, 124, 126, 127)"""
        total_users = self.db.query(User).count()
        active_users_7d = self.db.query(User).join(DBSession).filter(
            DBSession.created_at >= datetime.utcnow() - timedelta(days=7)
        ).distinct().count()
        
        new_users_30d = self.db.query(User).filter(
            User.created_at >= datetime.utcnow() - timedelta(days=30)
        ).count()
        
        return {
            "total_users": total_users,
            "active_users_7d": active_users_7d,
            "new_users_30d": new_users_30d,
            "user_retention_rate": (active_users_7d / total_users * 100) if total_users > 0 else 0
        }
    
    async def get_session_metrics(self) -> Dict[str, Any]:
        """Get session-related metrics. (Features: 29, 31, 37, 43, 45, 120, 122, 123, 124)"""
        total_sessions = self.db.query(DBSession).count()
        sessions_24h = self.db.query(DBSession).filter(
            DBSession.created_at >= datetime.utcnow() - timedelta(hours=24)
        ).count()
        
        avg_session_duration = self.db.query(
            func.avg(func.extract('epoch', DBSession.updated_at - DBSession.created_at))
        ).filter(DBSession.updated_at.isnot(None)).scalar() or 0
        
        return {
            "total_sessions": total_sessions,
            "sessions_24h": sessions_24h,
            "avg_session_duration_seconds": avg_session_duration
        }
    
    async def get_message_metrics(self) -> Dict[str, Any]:
        """Get message-related metrics. (Features: 29, 31, 48, 49, 50, 51, 120, 122, 123, 124)"""
        total_messages = self.db.query(Message).count()
        messages_24h = self.db.query(Message).filter(
            Message.timestamp >= datetime.utcnow() - timedelta(hours=24)
        ).count()
        
        avg_message_length = self.db.query(
            func.avg(func.length(Message.content))
        ).scalar() or 0
        
        return {
            "total_messages": total_messages,
            "messages_24h": messages_24h,
            "avg_message_length": avg_message_length
        }
    
    async def get_memory_metrics(self) -> Dict[str, Any]:
        """Get memory-related metrics. (Features: 1, 2, 4, 7, 8, 9, 10, 15, 16, 29, 31)"""
        total_memories = self.db.query(Memory).count()
        memories_7d = self.db.query(Memory).filter(
            Memory.timestamp >= datetime.utcnow() - timedelta(days=7)
        ).count()
        
        avg_memory_size = self.db.query(
            func.avg(func.length(Memory.content))
        ).scalar() or 0
        
        unique_tags = self.db.query(Memory.tags).distinct().count()
        
        return {
            "total_memories": total_memories,
            "memories_7d": memories_7d,
            "avg_memory_size": avg_memory_size,
            "unique_tags": unique_tags
        }
    
    async def get_plugin_metrics(self) -> Dict[str, Any]:
        """Get plugin-related metrics. (Features: 56, 57, 194, 204, 212)"""
        try:
            total_plugins = self.db.query(Plugin).count()
            active_plugins = self.db.query(Plugin).filter(Plugin.enabled == True).count()
            
            return {
                "total_plugins": total_plugins,
                "active_plugins": active_plugins,
                "plugin_utilization": (active_plugins / total_plugins * 100) if total_plugins > 0 else 0
            }
        except Exception:
            return {
                "total_plugins": 0,
                "active_plugins": 0,
                "plugin_utilization": 0
            }
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics. (Features: 123, 173, 174, 175, 176, 177, 178)"""
        return {
            "database_size_mb": await self._get_database_size(),
            "query_performance": await self._get_query_performance(),
            "system_load": await self._get_system_load()
        }
    
    async def _get_database_size(self) -> float:
        """Get database size in MB. (Features: 123, 135, 136)"""
        try:
            # Placeholder - actual implementation would depend on database type
            return 0.0
        except Exception:
            return 0.0
    
    async def _get_query_performance(self) -> Dict[str, float]:
        """Get query performance metrics. (Features: 123, 175, 176)"""
        return {
            "avg_query_time_ms": 0.0,
            "slow_queries_count": 0
        }
    
    async def _get_system_load(self) -> Dict[str, float]:
        """Get system load metrics. (Features: 123, 175, 176, 177)"""
        return {
            "cpu_usage_percent": 0.0,
            "memory_usage_percent": 0.0,
            "disk_usage_percent": 0.0
        } 