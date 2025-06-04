import statistics
from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def is_cache_valid(cache: Dict, cache_key: str, timeout: int) -> bool:
    """Check if cache entry is valid. (Features: 29, 31, 134)"""
    if cache_key not in cache:
        return False
    
    cached_time = cache[cache_key]["timestamp"]
    return (datetime.utcnow() - cached_time).total_seconds() < timeout

def cache_metrics(cache: Dict, cache_key: str, data: Any) -> None:
    """Cache metrics data with timestamp. (Features: 29, 31, 134)"""
    cache[cache_key] = {
        "data": data,
        "timestamp": datetime.utcnow()
    }

def calculate_growth_rate(periods: List[Dict]) -> float:
    """Calculate growth rate between periods. (Features: 29, 31, 120, 122, 123, 124)"""
    if len(periods) < 2:
        return 0.0
    
    try:
        values = [p["value"] for p in periods if "value" in p]
        if len(values) < 2:
            return 0.0
        
        first_value = values[0]
        last_value = values[-1]
        
        if first_value == 0:
            return 100.0 if last_value > 0 else 0.0
        
        return ((last_value - first_value) / first_value) * 100
    except Exception as e:
        logger.error(f"Error calculating growth rate: {e}")
        return 0.0

def calculate_engagement_score(sessions: List, messages: List) -> float:
    """Calculate user engagement score. (Features: 29, 31, 66, 76, 78, 80, 81, 201, 202, 203)"""
    if not sessions and not messages:
        return 0.0
    
    try:
        session_score = min(len(sessions) * 10, 40)  # Max 40 points for sessions
        message_score = min(len(messages) * 2, 60)   # Max 60 points for messages
        return min(session_score + message_score, 100.0)
    except Exception as e:
        logger.error(f"Error calculating engagement score: {e}")
        return 0.0

def safe_mean(values: List[float]) -> float:
    """Calculate mean safely, handling empty lists. (Features: 29, 31, 134)"""
    if not values:
        return 0.0
    try:
        return statistics.mean(values)
    except Exception:
        return 0.0

def safe_median(values: List[float]) -> float:
    """Calculate median safely, handling empty lists. (Features: 29, 31, 134)"""
    if not values:
        return 0.0
    try:
        return statistics.median(values)
    except Exception:
        return 0.0 