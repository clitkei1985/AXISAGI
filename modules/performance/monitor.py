import logging
import asyncio
import time
import psutil
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    network_io_bytes: Dict[str, int]
    process_count: int
    load_average: List[float]

@dataclass
class ApplicationMetrics:
    timestamp: datetime
    active_sessions: int
    total_requests: int
    avg_response_time: float
    error_rate: float
    cache_hit_rate: float
    database_connections: int
    queue_size: int

class PerformanceMonitor:
    def __init__(self):
        self.system_metrics: List[SystemMetrics] = []
        self.app_metrics: List[ApplicationMetrics] = []
        self.monitoring_active = False
        self.monitoring_task: Optional[asyncio.Task] = None
        self.metrics_retention_hours = 24
        self.collection_interval = 30  # seconds
        
        # Performance counters
        self.request_counter = 0
        self.error_counter = 0
        self.response_times: List[float] = []
        self.session_counter = 0
        
    async def start_monitoring(self):
        """Start the performance monitoring system"""
        if self.monitoring_active:
            logger.warning("Performance monitoring already active")
            return
            
        logger.info("Starting performance monitoring...")
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Performance monitoring started")
    
    async def stop_monitoring(self):
        """Stop the performance monitoring system"""
        if not self.monitoring_active:
            return
            
        logger.info("Stopping performance monitoring...")
        self.monitoring_active = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
                
        await self._save_metrics()
        logger.info("Performance monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        try:
            while self.monitoring_active:
                await self._collect_system_metrics()
                await self._collect_application_metrics()
                await self._cleanup_old_metrics()
                await asyncio.sleep(self.collection_interval)
        except asyncio.CancelledError:
            logger.info("Monitoring loop cancelled")
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
    
    async def _collect_system_metrics(self):
        """Collect system-level performance metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage_percent = disk.percent
            
            # Network I/O
            network = psutil.net_io_counters()
            network_io = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv
            }
            
            # Process count
            process_count = len(psutil.pids())
            
            # Load average (Unix-like systems)
            try:
                load_average = list(psutil.getloadavg())
            except AttributeError:
                load_average = [0.0, 0.0, 0.0]  # Windows fallback
            
            metrics = SystemMetrics(
                timestamp=datetime.utcnow(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                disk_usage_percent=disk_usage_percent,
                network_io_bytes=network_io,
                process_count=process_count,
                load_average=load_average
            )
            
            self.system_metrics.append(metrics)
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    async def _collect_application_metrics(self):
        """Collect application-level performance metrics"""
        try:
            # Calculate average response time
            avg_response_time = 0.0
            if self.response_times:
                avg_response_time = sum(self.response_times) / len(self.response_times)
                self.response_times.clear()  # Reset for next collection
            
            # Calculate error rate
            error_rate = 0.0
            if self.request_counter > 0:
                error_rate = (self.error_counter / self.request_counter) * 100
            
            metrics = ApplicationMetrics(
                timestamp=datetime.utcnow(),
                active_sessions=self.session_counter,
                total_requests=self.request_counter,
                avg_response_time=avg_response_time,
                error_rate=error_rate,
                cache_hit_rate=0.0,  # Placeholder
                database_connections=0,  # Placeholder
                queue_size=0  # Placeholder
            )
            
            self.app_metrics.append(metrics)
            
            # Reset counters for next period
            self.request_counter = 0
            self.error_counter = 0
            
        except Exception as e:
            logger.error(f"Error collecting application metrics: {e}")
    
    async def _cleanup_old_metrics(self):
        """Remove metrics older than retention period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.metrics_retention_hours)
        
        self.system_metrics = [
            m for m in self.system_metrics 
            if m.timestamp > cutoff_time
        ]
        
        self.app_metrics = [
            m for m in self.app_metrics 
            if m.timestamp > cutoff_time
        ]
    
    async def _save_metrics(self):
        """Save metrics to disk for persistence"""
        try:
            metrics_dir = Path("data/performance")
            metrics_dir.mkdir(parents=True, exist_ok=True)
            
            # Save system metrics
            system_file = metrics_dir / "system_metrics.json"
            system_data = [asdict(m) for m in self.system_metrics[-100:]]  # Last 100 records
            with open(system_file, 'w') as f:
                json.dump(system_data, f, default=str, indent=2)
            
            # Save application metrics
            app_file = metrics_dir / "app_metrics.json"
            app_data = [asdict(m) for m in self.app_metrics[-100:]]  # Last 100 records
            with open(app_file, 'w') as f:
                json.dump(app_data, f, default=str, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
    
    def record_request(self, response_time: float, is_error: bool = False):
        """Record a request for metrics"""
        self.request_counter += 1
        self.response_times.append(response_time)
        if is_error:
            self.error_counter += 1
    
    def record_session(self, active_count: int):
        """Record session count"""
        self.session_counter = active_count
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        latest_system = self.system_metrics[-1] if self.system_metrics else None
        latest_app = self.app_metrics[-1] if self.app_metrics else None
        
        return {
            "system": asdict(latest_system) if latest_system else None,
            "application": asdict(latest_app) if latest_app else None,
            "monitoring_active": self.monitoring_active,
            "metrics_count": {
                "system": len(self.system_metrics),
                "application": len(self.app_metrics)
            }
        }

# Global monitor instance
_performance_monitor = None

def get_performance_monitor() -> PerformanceMonitor:
    """Get or create the performance monitor instance"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor

async def start_monitoring():
    """Initialize and start performance monitoring"""
    try:
        logger.info("Initializing performance monitoring...")
        monitor = get_performance_monitor()
        await monitor.start_monitoring()
        logger.info("Performance monitoring initialized")
    except Exception as e:
        logger.error(f"Performance monitoring initialization failed: {e}")
        raise

async def stop_monitoring():
    """Stop performance monitoring"""
    try:
        monitor = get_performance_monitor()
        await monitor.stop_monitoring()
        logger.info("Performance monitoring stopped")
    except Exception as e:
        logger.error(f"Performance monitoring stop failed: {e}")
        raise
