from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from core.database import Session as DBSession, Message
from .utils import safe_mean
import logging

logger = logging.getLogger(__name__)

class ChatAnalytics:
    """Analyzes chat sessions and conversation patterns. (Features: 29, 31, 48, 49, 50, 51, 66, 80, 81, 134, 201, 202, 203)"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def collect_for_session(self, session_id: int) -> Dict[str, Any]:
        """Collect comprehensive analytics for a specific chat session. (Features: 29, 31, 48, 49, 50, 51, 66, 80, 81, 134)"""
        session = self.db.query(DBSession).filter(DBSession.id == session_id).first()
        if not session:
            raise ValueError("Session not found")
        
        messages = self.db.query(Message).filter(
            Message.session_id == session_id
        ).order_by(Message.timestamp.asc()).all()
        
        user_messages = [m for m in messages if m.role == "user"]
        assistant_messages = [m for m in messages if m.role == "assistant"]
        
        return {
            "session_id": session_id,
            "session_info": {
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat() if session.updated_at else None,
                "duration": self._calculate_session_duration(session),
                "session_type": session.session_type
            },
            "message_stats": {
                "total_messages": len(messages),
                "user_messages": len(user_messages),
                "assistant_messages": len(assistant_messages),
                "avg_user_message_length": safe_mean([len(m.content) for m in user_messages]),
                "avg_assistant_message_length": safe_mean([len(m.content) for m in assistant_messages]),
                "message_frequency": self._calculate_message_frequency(messages)
            },
            "conversation_flow": self._analyze_conversation_flow(messages),
            "topics": self._extract_topics(messages),
            "sentiment": self._analyze_sentiment_trends(messages),
            "interaction_patterns": self._analyze_interaction_patterns(messages)
        }
    
    def _calculate_session_duration(self, session) -> float:
        """Calculate session duration in seconds. (Features: 29, 31, 37, 43)"""
        if not session.updated_at:
            return 0.0
        return (session.updated_at - session.created_at).total_seconds()
    
    def _calculate_message_frequency(self, messages: List) -> float:
        """Calculate messages per minute. (Features: 29, 31, 48, 49)"""
        if len(messages) < 2:
            return 0.0
        
        first_message = messages[0]
        last_message = messages[-1]
        duration_minutes = (last_message.timestamp - first_message.timestamp).total_seconds() / 60
        
        return len(messages) / duration_minutes if duration_minutes > 0 else 0.0
    
    def _analyze_conversation_flow(self, messages: List) -> Dict[str, Any]:
        """Analyze conversation flow and patterns. (Features: 29, 31, 48, 49, 63, 64, 66)"""
        if not messages:
            return {"flow_type": "empty"}
        
        # Analyze turn-taking patterns
        turns = []
        current_role = None
        turn_length = 0
        
        for message in messages:
            if message.role != current_role:
                if current_role is not None:
                    turns.append({"role": current_role, "length": turn_length})
                current_role = message.role
                turn_length = 1
            else:
                turn_length += 1
        
        if current_role is not None:
            turns.append({"role": current_role, "length": turn_length})
        
        # Analyze conversation phases
        phases = self._identify_conversation_phases(messages)
        
        return {
            "total_turns": len(turns),
            "avg_turn_length": safe_mean([t["length"] for t in turns]),
            "conversation_phases": phases,
            "flow_pattern": self._classify_flow_pattern(turns),
            "engagement_level": self._calculate_conversation_engagement(messages)
        }
    
    def _extract_topics(self, messages: List) -> List[str]:
        """Extract main topics from conversation. (Features: 29, 31, 63, 66, 78, 201, 202, 203)"""
        if not messages:
            return []
        
        # Simple keyword-based topic extraction
        topics = set()
        common_topics = {
            "programming": ["code", "python", "javascript", "function", "variable", "debug"],
            "data": ["data", "database", "sql", "analysis", "visualization"],
            "ai": ["ai", "machine learning", "neural network", "model", "training"],
            "web": ["html", "css", "website", "frontend", "backend", "api"],
            "help": ["help", "assistance", "problem", "issue", "error"],
            "learning": ["learn", "understand", "explain", "tutorial", "guide"]
        }
        
        all_content = " ".join([m.content.lower() for m in messages])
        
        for topic, keywords in common_topics.items():
            if any(keyword in all_content for keyword in keywords):
                topics.add(topic)
        
        return list(topics)
    
    def _analyze_sentiment_trends(self, messages: List) -> Dict[str, Any]:
        """Analyze sentiment trends in conversation. (Features: 29, 31, 66, 80, 81, 146, 199)"""
        if not messages:
            return {"overall": "neutral", "trends": []}
        
        # Simple sentiment analysis based on keywords
        positive_words = ["good", "great", "excellent", "perfect", "amazing", "helpful", "thanks"]
        negative_words = ["bad", "terrible", "awful", "wrong", "error", "problem", "issue"]
        
        sentiments = []
        for message in messages:
            if message.role == "user":
                content = message.content.lower()
                positive_count = sum(1 for word in positive_words if word in content)
                negative_count = sum(1 for word in negative_words if word in content)
                
                if positive_count > negative_count:
                    sentiment = "positive"
                elif negative_count > positive_count:
                    sentiment = "negative"
                else:
                    sentiment = "neutral"
                
                sentiments.append({
                    "timestamp": message.timestamp.isoformat(),
                    "sentiment": sentiment,
                    "confidence": abs(positive_count - negative_count) / max(1, len(content.split()))
                })
        
        # Calculate overall sentiment
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        for s in sentiments:
            sentiment_counts[s["sentiment"]] += 1
        
        overall = max(sentiment_counts.keys(), key=lambda k: sentiment_counts[k])
        
        return {
            "overall": overall,
            "sentiment_distribution": sentiment_counts,
            "trends": sentiments[-10:]  # Last 10 sentiment data points
        }
    
    def _analyze_interaction_patterns(self, messages: List) -> Dict[str, Any]:
        """Analyze interaction patterns and styles. (Features: 29, 31, 66, 80, 81, 201, 202, 203)"""
        if not messages:
            return {"pattern": "none"}
        
        user_messages = [m for m in messages if m.role == "user"]
        assistant_messages = [m for m in messages if m.role == "assistant"]
        
        # Calculate response times (simplified)
        response_times = []
        for i in range(len(messages) - 1):
            if messages[i].role == "user" and messages[i + 1].role == "assistant":
                response_time = (messages[i + 1].timestamp - messages[i].timestamp).total_seconds()
                response_times.append(response_time)
        
        # Analyze question patterns
        questions = [m for m in user_messages if "?" in m.content]
        
        return {
            "avg_response_time_seconds": safe_mean(response_times),
            "question_ratio": len(questions) / len(user_messages) if user_messages else 0,
            "interaction_style": self._classify_interaction_style(user_messages),
            "conversation_depth": self._calculate_conversation_depth(messages),
            "follow_up_ratio": self._calculate_follow_up_ratio(messages)
        }
    
    def _identify_conversation_phases(self, messages: List) -> List[str]:
        """Identify different phases in conversation. (Features: 29, 31, 63, 64, 66)"""
        if len(messages) < 3:
            return ["brief"]
        
        phases = []
        
        # Simple phase detection based on message patterns
        if len(messages) <= 5:
            phases.append("opening")
        elif len(messages) <= 15:
            phases.extend(["opening", "main"])
        else:
            phases.extend(["opening", "main", "development"])
        
        return phases
    
    def _classify_flow_pattern(self, turns: List) -> str:
        """Classify conversation flow pattern. (Features: 29, 31, 63, 64, 66)"""
        if not turns:
            return "none"
        
        avg_turn_length = safe_mean([t["length"] for t in turns])
        
        if avg_turn_length < 1.5:
            return "rapid_exchange"
        elif avg_turn_length < 3:
            return "balanced"
        else:
            return "extended_turns"
    
    def _calculate_conversation_engagement(self, messages: List) -> float:
        """Calculate engagement level of conversation. (Features: 29, 31, 66, 76, 78, 80, 81)"""
        if not messages:
            return 0.0
        
        user_messages = [m for m in messages if m.role == "user"]
        if not user_messages:
            return 0.0
        
        # Factors that indicate engagement
        message_count_score = min(len(user_messages) * 10, 50)  # Max 50 points
        avg_length_score = min(safe_mean([len(m.content) for m in user_messages]) / 10, 30)  # Max 30 points
        question_score = min(sum(1 for m in user_messages if "?" in m.content) * 5, 20)  # Max 20 points
        
        return min(message_count_score + avg_length_score + question_score, 100.0)
    
    def _classify_interaction_style(self, user_messages: List) -> str:
        """Classify user's interaction style. (Features: 66, 80, 81, 201, 202, 203)"""
        if not user_messages:
            return "unknown"
        
        avg_length = safe_mean([len(m.content) for m in user_messages])
        question_ratio = sum(1 for m in user_messages if "?" in m.content) / len(user_messages)
        
        if question_ratio > 0.5:
            return "question_focused"
        elif avg_length > 100:
            return "detailed"
        elif avg_length < 30:
            return "concise"
        else:
            return "balanced"
    
    def _calculate_conversation_depth(self, messages: List) -> int:
        """Calculate depth of conversation topics. (Features: 29, 31, 63, 66, 78)"""
        # Simple depth calculation based on message count and back-references
        if len(messages) < 5:
            return 1
        elif len(messages) < 15:
            return 2
        else:
            return 3
    
    def _calculate_follow_up_ratio(self, messages: List) -> float:
        """Calculate ratio of follow-up questions/comments. (Features: 29, 31, 66)"""
        if len(messages) < 2:
            return 0.0
        
        follow_ups = 0
        user_messages = [m for m in messages if m.role == "user"]
        
        for i in range(1, len(user_messages)):
            current = user_messages[i].content.lower()
            if any(phrase in current for phrase in ["also", "additionally", "furthermore", "what about", "how about"]):
                follow_ups += 1
        
        return follow_ups / len(user_messages) if user_messages else 0.0 