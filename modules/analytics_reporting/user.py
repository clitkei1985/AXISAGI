from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
from core.database import User, Session as DBSession, Message, Memory
from .utils import calculate_engagement_score, safe_mean
import logging

logger = logging.getLogger(__name__)

class UserAnalytics:
    """Analyzes user behavior, engagement, and retention. (Features: 29, 31, 66, 76, 78, 80, 81, 126, 127, 134, 188, 201, 202, 203)"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def collect_for_user(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Collect comprehensive analytics for a specific user. (Features: 29, 31, 66, 76, 78, 80, 81, 134, 201, 202, 203)"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # User sessions
        sessions = self.db.query(DBSession).filter(
            and_(
                DBSession.user_id == user_id,
                DBSession.created_at >= start_date
            )
        ).all()
        
        # Messages
        session_ids = [s.id for s in sessions]
        messages = self.db.query(Message).filter(
            and_(
                Message.session_id.in_(session_ids),
                Message.timestamp >= start_date
            )
        ).all() if session_ids else []
        
        # Memories
        memories = self.db.query(Memory).filter(
            and_(
                Memory.user_id == user_id,
                Memory.timestamp >= start_date
            )
        ).all()
        
        return {
            "user_id": user_id,
            "username": user.username,
            "period_days": days,
            "activity": self.analyze_user_activity(sessions, messages, memories),
            "usage_patterns": self.analyze_usage_patterns(sessions, messages),
            "memory_usage": self.analyze_memory_usage(memories),
            "engagement_score": calculate_engagement_score(sessions, messages),
            "behavior_insights": self.analyze_behavior_patterns(sessions, messages, memories)
        }
    
    def analyze_user_activity(self, sessions: List, messages: List, memories: List) -> Dict[str, Any]:
        """Analyze user activity patterns. (Features: 29, 31, 66, 80, 81, 201, 202, 203)"""
        return {
            "total_sessions": len(sessions),
            "total_messages": len(messages),
            "total_memories": len(memories),
            "avg_sessions_per_day": len(sessions) / 30 if sessions else 0,
            "avg_messages_per_session": len(messages) / len(sessions) if sessions else 0,
            "most_active_hours": self._get_most_active_hours(sessions),
            "activity_consistency": self._calculate_activity_consistency(sessions)
        }
    
    def analyze_usage_patterns(self, sessions: List, messages: List) -> Dict[str, Any]:
        """Analyze user usage patterns. (Features: 29, 31, 66, 76, 78, 80, 81, 201, 202, 203)"""
        if not sessions:
            return {"pattern": "inactive"}
        
        session_durations = [
            (s.updated_at - s.created_at).total_seconds() 
            for s in sessions if s.updated_at
        ]
        
        message_lengths = [len(m.content) for m in messages if m.role == "user"]
        
        return {
            "avg_session_duration": safe_mean(session_durations),
            "session_frequency": len(sessions) / 30,
            "preferred_session_length": "short" if safe_mean(session_durations) < 300 else "long",
            "communication_style": self._analyze_communication_style(message_lengths),
            "usage_consistency": self._calculate_usage_consistency(sessions)
        }
    
    def analyze_memory_usage(self, memories: List) -> Dict[str, Any]:
        """Analyze user memory patterns. (Features: 1, 2, 4, 7, 8, 9, 10, 15, 16, 29, 31)"""
        if not memories:
            return {"total": 0, "patterns": "no_memories"}
        
        memory_sizes = [len(m.content) for m in memories]
        tags_used = set()
        for m in memories:
            if m.tags:
                tags_used.update(m.tags if isinstance(m.tags, list) else [m.tags])
        
        return {
            "total_memories": len(memories),
            "avg_memory_size": safe_mean(memory_sizes),
            "unique_tags": len(tags_used),
            "memory_growth_rate": self._calculate_memory_growth_rate(memories),
            "memory_categories": self._categorize_memories(memories)
        }
    
    def analyze_behavior_patterns(self, sessions: List, messages: List, memories: List) -> Dict[str, Any]:
        """Analyze deeper behavioral patterns. (Features: 66, 76, 78, 80, 81, 188, 201, 202, 203)"""
        return {
            "user_type": self._classify_user_type(sessions, messages, memories),
            "learning_pattern": self._analyze_learning_pattern(messages, memories),
            "interaction_style": self._analyze_interaction_style(messages),
            "feature_usage": self._analyze_feature_usage(sessions, messages, memories)
        }
    
    def _get_most_active_hours(self, sessions: List) -> List[int]:
        """Get hours when user is most active. (Features: 29, 31, 34, 203)"""
        if not sessions:
            return []
        
        hour_counts = {}
        for session in sessions:
            hour = session.created_at.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        return sorted(hour_counts.keys(), key=lambda h: hour_counts[h], reverse=True)[:3]
    
    def _calculate_activity_consistency(self, sessions: List) -> float:
        """Calculate how consistent user activity is. (Features: 29, 31, 203)"""
        if len(sessions) < 2:
            return 0.0
        
        # Group by day
        daily_counts = {}
        for session in sessions:
            day = session.created_at.date()
            daily_counts[day] = daily_counts.get(day, 0) + 1
        
        if not daily_counts:
            return 0.0
        
        values = list(daily_counts.values())
        if len(values) == 1:
            return 100.0
        
        # Calculate coefficient of variation (lower = more consistent)
        mean_val = safe_mean(values)
        if mean_val == 0:
            return 0.0
        
        variance = sum((x - mean_val) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5
        cv = std_dev / mean_val
        
        # Convert to consistency score (0-100)
        return max(0, 100 - (cv * 100))
    
    def _analyze_communication_style(self, message_lengths: List[int]) -> str:
        """Analyze user's communication style. (Features: 66, 80, 81, 201, 202, 203)"""
        if not message_lengths:
            return "unknown"
        
        avg_length = safe_mean(message_lengths)
        
        if avg_length < 20:
            return "concise"
        elif avg_length < 100:
            return "moderate"
        else:
            return "verbose"
    
    def _calculate_usage_consistency(self, sessions: List) -> float:
        """Calculate usage consistency over time. (Features: 29, 31, 203)"""
        return self._calculate_activity_consistency(sessions)
    
    def _calculate_memory_growth_rate(self, memories: List) -> float:
        """Calculate how fast user's memory is growing. (Features: 16, 29, 31)"""
        if len(memories) < 2:
            return 0.0
        
        # Sort by timestamp
        sorted_memories = sorted(memories, key=lambda m: m.timestamp)
        
        # Calculate memories per week
        first_date = sorted_memories[0].timestamp
        last_date = sorted_memories[-1].timestamp
        weeks = max(1, (last_date - first_date).days / 7)
        
        return len(memories) / weeks
    
    def _categorize_memories(self, memories: List) -> Dict[str, int]:
        """Categorize memories by type or content. (Features: 17, 29, 31)"""
        categories = {"personal": 0, "work": 0, "learning": 0, "other": 0}
        
        for memory in memories:
            content = memory.content.lower()
            if any(word in content for word in ["personal", "family", "friend"]):
                categories["personal"] += 1
            elif any(word in content for word in ["work", "project", "meeting"]):
                categories["work"] += 1
            elif any(word in content for word in ["learn", "study", "research"]):
                categories["learning"] += 1
            else:
                categories["other"] += 1
        
        return categories
    
    def _classify_user_type(self, sessions: List, messages: List, memories: List) -> str:
        """Classify user based on behavior patterns. (Features: 66, 188, 201, 202, 203)"""
        if not sessions:
            return "inactive"
        
        avg_sessions_per_week = len(sessions) / 4
        avg_messages_per_session = len(messages) / len(sessions) if sessions else 0
        memory_ratio = len(memories) / len(sessions) if sessions else 0
        
        if avg_sessions_per_week > 5 and avg_messages_per_session > 10:
            return "power_user"
        elif avg_sessions_per_week > 2 and memory_ratio > 0.5:
            return "regular_learner"
        elif avg_sessions_per_week > 1:
            return "casual_user"
        else:
            return "occasional_user"
    
    def _analyze_learning_pattern(self, messages: List, memories: List) -> str:
        """Analyze how user learns and retains information. (Features: 76, 78, 188, 201, 202, 203)"""
        if not messages and not memories:
            return "unknown"
        
        question_count = sum(1 for m in messages if m.role == "user" and "?" in m.content)
        total_user_messages = sum(1 for m in messages if m.role == "user")
        
        if total_user_messages == 0:
            return "passive"
        
        question_ratio = question_count / total_user_messages
        memory_ratio = len(memories) / total_user_messages if total_user_messages > 0 else 0
        
        if question_ratio > 0.3 and memory_ratio > 0.2:
            return "active_learner"
        elif question_ratio > 0.3:
            return "curious"
        elif memory_ratio > 0.2:
            return "knowledge_collector"
        else:
            return "casual"
    
    def _analyze_interaction_style(self, messages: List) -> str:
        """Analyze user's interaction style. (Features: 66, 80, 81, 201, 202, 203)"""
        user_messages = [m for m in messages if m.role == "user"]
        if not user_messages:
            return "unknown"
        
        avg_length = safe_mean([len(m.content) for m in user_messages])
        question_ratio = sum(1 for m in user_messages if "?" in m.content) / len(user_messages)
        
        if avg_length > 100 and question_ratio > 0.3:
            return "detailed_inquirer"
        elif avg_length > 100:
            return "detailed_communicator"
        elif question_ratio > 0.5:
            return "question_focused"
        else:
            return "direct_communicator"
    
    def _analyze_feature_usage(self, sessions: List, messages: List, memories: List) -> Dict[str, bool]:
        """Analyze which features user actively uses. (Features: 29, 31, 188, 201, 202, 203)"""
        return {
            "uses_memory": len(memories) > 0,
            "multi_session_user": len(sessions) > 1,
            "active_communicator": len(messages) > 10,
            "consistent_user": len(sessions) > 5
        } 