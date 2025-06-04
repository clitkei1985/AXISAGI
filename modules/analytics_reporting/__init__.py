"""
Analytics and Reporting Module

Modular analytics system for comprehensive data collection, analysis, and reporting.
Implements features 29, 31, 55, 66, 76, 78, 80, 81, 111, 120, 122, 123, 124, 126, 127, 
129, 133, 134, 135, 136, 146, 149, 150, 151, 175, 176, 177, 178, 188, 199, 201, 202, 203
"""

from .collector import AnalyticsCollector, get_analytics_collector
from .system import SystemMetrics
from .user import UserAnalytics
from .chat import ChatAnalytics
from .reports import ReportGenerator
from .utils import (
    is_cache_valid,
    cache_metrics,
    calculate_growth_rate,
    calculate_engagement_score,
    safe_mean,
    safe_median
)

__all__ = [
    "AnalyticsCollector",
    "get_analytics_collector",
    "SystemMetrics", 
    "UserAnalytics",
    "ChatAnalytics",
    "ReportGenerator",
    "is_cache_valid",
    "cache_metrics",
    "calculate_growth_rate",
    "calculate_engagement_score",
    "safe_mean",
    "safe_median"
]
