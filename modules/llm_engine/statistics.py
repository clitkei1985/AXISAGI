from typing import Dict, Optional
import time
from datetime import datetime, timedelta
import logging
from .schemas import ModelStats

logger = logging.getLogger(__name__)

class LLMStatistics:
    """Handles performance tracking and statistics for LLM operations."""
    
    def __init__(self):
        self.stats = {
            "total_requests": 0,
            "total_tokens": 0,
            "total_latency": 0,
            "errors": 0,
            "last_error": None,
            "last_error_time": None,
            "start_time": time.time(),
            "model_usage": {},
            "request_types": {},
            "hourly_stats": {},
            "daily_stats": {}
        }
        
    def update_stats(
        self, 
        latency: float = 0, 
        tokens: int = 0, 
        error: str = None, 
        success: bool = True,
        model_name: str = None,
        request_type: str = "completion"
    ):
        """Update usage statistics."""
        self.stats["total_requests"] += 1
        self.stats["total_tokens"] += tokens
        self.stats["total_latency"] += latency
        
        # Track model usage
        if model_name:
            if model_name not in self.stats["model_usage"]:
                self.stats["model_usage"][model_name] = {
                    "requests": 0,
                    "tokens": 0,
                    "latency": 0,
                    "errors": 0
                }
            self.stats["model_usage"][model_name]["requests"] += 1
            self.stats["model_usage"][model_name]["tokens"] += tokens
            self.stats["model_usage"][model_name]["latency"] += latency
            if not success:
                self.stats["model_usage"][model_name]["errors"] += 1
        
        # Track request types
        if request_type not in self.stats["request_types"]:
            self.stats["request_types"][request_type] = 0
        self.stats["request_types"][request_type] += 1
        
        # Track hourly stats
        current_hour = datetime.utcnow().strftime("%Y-%m-%d-%H")
        if current_hour not in self.stats["hourly_stats"]:
            self.stats["hourly_stats"][current_hour] = {
                "requests": 0,
                "tokens": 0,
                "latency": 0,
                "errors": 0
            }
        self.stats["hourly_stats"][current_hour]["requests"] += 1
        self.stats["hourly_stats"][current_hour]["tokens"] += tokens
        self.stats["hourly_stats"][current_hour]["latency"] += latency
        
        # Track daily stats
        current_day = datetime.utcnow().strftime("%Y-%m-%d")
        if current_day not in self.stats["daily_stats"]:
            self.stats["daily_stats"][current_day] = {
                "requests": 0,
                "tokens": 0,
                "latency": 0,
                "errors": 0
            }
        self.stats["daily_stats"][current_day]["requests"] += 1
        self.stats["daily_stats"][current_day]["tokens"] += tokens
        self.stats["daily_stats"][current_day]["latency"] += latency
        
        if not success:
            self.stats["errors"] += 1
            self.stats["last_error"] = error
            self.stats["last_error_time"] = datetime.utcnow()
            self.stats["hourly_stats"][current_hour]["errors"] += 1
            self.stats["daily_stats"][current_day]["errors"] += 1

    def get_stats(self) -> ModelStats:
        """Get current model statistics."""
        total_reqs = self.stats["total_requests"] or 1  # Avoid division by zero
        return ModelStats(
            total_requests=self.stats["total_requests"],
            total_tokens=self.stats["total_tokens"],
            avg_latency_ms=self.stats["total_latency"] / total_reqs,
            error_rate=self.stats["errors"] / total_reqs,
            last_error=self.stats["last_error"],
            last_error_time=self.stats["last_error_time"],
            uptime_seconds=int(time.time() - self.stats["start_time"])
        )

    def get_detailed_stats(self) -> Dict:
        """Get detailed statistics including model-specific and time-based data."""
        total_reqs = self.stats["total_requests"] or 1
        
        return {
            "overview": {
                "total_requests": self.stats["total_requests"],
                "total_tokens": self.stats["total_tokens"],
                "avg_latency_ms": self.stats["total_latency"] / total_reqs,
                "error_rate": self.stats["errors"] / total_reqs,
                "uptime_seconds": int(time.time() - self.stats["start_time"]),
                "requests_per_hour": self._calculate_requests_per_hour(),
                "tokens_per_second": self._calculate_tokens_per_second()
            },
            "model_usage": self._format_model_usage(),
            "request_types": self.stats["request_types"],
            "recent_activity": self._get_recent_activity(),
            "performance_trends": self._get_performance_trends(),
            "error_summary": {
                "total_errors": self.stats["errors"],
                "last_error": self.stats["last_error"],
                "last_error_time": self.stats["last_error_time"],
                "error_rate": self.stats["errors"] / total_reqs
            }
        }

    def _format_model_usage(self) -> Dict:
        """Format model usage statistics."""
        formatted = {}
        for model, stats in self.stats["model_usage"].items():
            requests = stats["requests"] or 1
            formatted[model] = {
                "requests": stats["requests"],
                "tokens": stats["tokens"],
                "avg_latency_ms": stats["latency"] / requests,
                "error_rate": stats["errors"] / requests,
                "avg_tokens_per_request": stats["tokens"] / requests
            }
        return formatted

    def _calculate_requests_per_hour(self) -> float:
        """Calculate average requests per hour."""
        uptime_hours = (time.time() - self.stats["start_time"]) / 3600
        if uptime_hours < 0.01:  # Less than 36 seconds
            return 0.0
        return self.stats["total_requests"] / uptime_hours

    def _calculate_tokens_per_second(self) -> float:
        """Calculate average tokens per second."""
        uptime_seconds = time.time() - self.stats["start_time"]
        if uptime_seconds < 1:
            return 0.0
        return self.stats["total_tokens"] / uptime_seconds

    def _get_recent_activity(self) -> Dict:
        """Get activity for the last 24 hours."""
        now = datetime.utcnow()
        last_24h = []
        
        for i in range(24):
            hour = (now - timedelta(hours=i)).strftime("%Y-%m-%d-%H")
            stats = self.stats["hourly_stats"].get(hour, {
                "requests": 0, "tokens": 0, "latency": 0, "errors": 0
            })
            last_24h.append({
                "hour": hour,
                "requests": stats["requests"],
                "tokens": stats["tokens"],
                "avg_latency": stats["latency"] / max(stats["requests"], 1),
                "errors": stats["errors"]
            })
        
        return {"last_24_hours": list(reversed(last_24h))}

    def _get_performance_trends(self) -> Dict:
        """Analyze performance trends over time."""
        if len(self.stats["hourly_stats"]) < 2:
            return {"trend": "insufficient_data"}
        
        recent_hours = sorted(self.stats["hourly_stats"].keys())[-12:]  # Last 12 hours
        if len(recent_hours) < 2:
            return {"trend": "insufficient_data"}
        
        # Calculate average latency for first and second half
        mid_point = len(recent_hours) // 2
        first_half_latency = []
        second_half_latency = []
        
        for hour in recent_hours[:mid_point]:
            stats = self.stats["hourly_stats"][hour]
            if stats["requests"] > 0:
                first_half_latency.append(stats["latency"] / stats["requests"])
        
        for hour in recent_hours[mid_point:]:
            stats = self.stats["hourly_stats"][hour]
            if stats["requests"] > 0:
                second_half_latency.append(stats["latency"] / stats["requests"])
        
        if not first_half_latency or not second_half_latency:
            return {"trend": "insufficient_data"}
        
        avg_first = sum(first_half_latency) / len(first_half_latency)
        avg_second = sum(second_half_latency) / len(second_half_latency)
        
        change_percent = ((avg_second - avg_first) / avg_first) * 100
        
        if change_percent > 10:
            trend = "degrading"
        elif change_percent < -10:
            trend = "improving"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "latency_change_percent": change_percent,
            "avg_latency_first_half": avg_first,
            "avg_latency_second_half": avg_second
        }

    def reset_stats(self):
        """Reset all statistics."""
        self.stats = {
            "total_requests": 0,
            "total_tokens": 0,
            "total_latency": 0,
            "errors": 0,
            "last_error": None,
            "last_error_time": None,
            "start_time": time.time(),
            "model_usage": {},
            "request_types": {},
            "hourly_stats": {},
            "daily_stats": {}
        }
        logger.info("LLM statistics reset")

    def cleanup_old_stats(self, days_to_keep: int = 7):
        """Clean up old hourly and daily statistics."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Clean hourly stats
        cutoff_hour = cutoff_date.strftime("%Y-%m-%d-%H")
        hours_to_remove = [
            hour for hour in self.stats["hourly_stats"].keys()
            if hour < cutoff_hour
        ]
        for hour in hours_to_remove:
            del self.stats["hourly_stats"][hour]
        
        # Clean daily stats
        cutoff_day = cutoff_date.strftime("%Y-%m-%d")
        days_to_remove = [
            day for day in self.stats["daily_stats"].keys()
            if day < cutoff_day
        ]
        for day in days_to_remove:
            del self.stats["daily_stats"][day]
        
        if hours_to_remove or days_to_remove:
            logger.info(f"Cleaned up {len(hours_to_remove)} hourly and {len(days_to_remove)} daily stats older than {days_to_keep} days")

    def export_stats(self) -> Dict:
        """Export all statistics for backup or analysis."""
        return {
            "export_time": datetime.utcnow().isoformat(),
            "stats": self.stats.copy()
        }

    def import_stats(self, exported_stats: Dict):
        """Import previously exported statistics."""
        if "stats" in exported_stats:
            self.stats.update(exported_stats["stats"])
            logger.info("Imported LLM statistics")
        else:
            logger.error("Invalid stats format for import")
