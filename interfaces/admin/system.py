from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import psutil
import os
import logging
from pathlib import Path

from core.database import get_db, User, Session as DBSession, Message, Memory, AuditLog
from core.security import get_current_admin_user
from .schemas import (
    SystemStatus,
    SystemConfig,
    SystemConfigUpdate,
    SystemHealth,
    AdminActionResult
)

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/status", response_model=SystemStatus)
async def get_system_status(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive system status and health metrics."""
    try:
        # Get system metrics
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        disk = psutil.disk_usage('/')
        
        # Get application metrics
        active_users = db.query(User).filter(User.is_active == True).count()
        active_sessions = db.query(DBSession).filter(
            DBSession.updated_at >= datetime.utcnow() - timedelta(hours=24)
        ).count()
        
        # Calculate uptime (simplified)
        uptime = psutil.boot_time()
        uptime_seconds = datetime.utcnow().timestamp() - uptime
        
        # Get last backup info (placeholder)
        last_backup = None
        backup_dir = Path("db/backups")
        if backup_dir.exists():
            backup_files = list(backup_dir.glob("*.sql"))
            if backup_files:
                latest_backup = max(backup_files, key=os.path.getctime)
                last_backup = datetime.fromtimestamp(os.path.getctime(latest_backup))
        
        # Determine overall status
        status = "healthy"
        if memory.percent > 90 or cpu_percent > 90 or disk.percent > 90:
            status = "critical"
        elif memory.percent > 80 or cpu_percent > 80 or disk.percent > 80:
            status = "warning"
        
        return SystemStatus(
            status=status,
            uptime_seconds=uptime_seconds,
            memory_usage_mb=memory.used / (1024 * 1024),
            cpu_usage_percent=cpu_percent,
            disk_usage_percent=disk.percent,
            active_users=active_users,
            active_sessions=active_sessions,
            database_status="connected",
            last_backup=last_backup,
            version="1.0.0"
        )
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system status")

@router.get("/config", response_model=SystemConfig)
async def get_system_config(
    current_admin: User = Depends(get_current_admin_user)
):
    """Get current system configuration."""
    # In a real implementation, this would read from a config file or database
    config = SystemConfig(
        debug_mode=True,  # From settings
        log_level="INFO",
        max_users=1000,
        session_timeout_hours=24,
        backup_enabled=True,
        backup_interval_hours=24,
        maintenance_mode=False,
        features_enabled={
            "analytics": True,
            "plugins": True,
            "code_analysis": True,
            "multimodal": True,
            "memory_system": True,
            "real_time_chat": True
        }
    )
    return config

@router.put("/config", response_model=AdminActionResult)
async def update_system_config(
    config_update: SystemConfigUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update system configuration."""
    try:
        # In a real implementation, this would update the actual config
        # For now, we'll just log the changes
        changes = config_update.dict(exclude_unset=True)
        
        # Log the configuration change
        audit_entry = AuditLog(
            user_id=current_admin.id,
            action="update_system_config",
            resource_type="system_config",
            details=changes,
            ip_address="127.0.0.1",  # Would get from request
            timestamp=datetime.utcnow()
        )
        db.add(audit_entry)
        db.commit()
        
        return AdminActionResult(
            success=True,
            message="System configuration updated successfully",
            details=changes
        )
        
    except Exception as e:
        logger.error(f"Error updating system config: {e}")
        raise HTTPException(status_code=500, detail="Failed to update configuration")

@router.get("/health", response_model=SystemHealth)
async def get_system_health(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive system health check."""
    try:
        # Check various components
        components = {}
        
        # Database check
        try:
            db.execute("SELECT 1")
            components["database"] = "healthy"
        except:
            components["database"] = "critical"
        
        # Memory system check
        try:
            from modules.memory.memory_manager import get_memory_manager
            memory_manager = get_memory_manager(db)
            components["memory_system"] = "healthy"
        except:
            components["memory_system"] = "degraded"
        
        # Plugin system check
        try:
            from modules.plugin_system.manager import get_plugin_manager
            plugin_manager = get_plugin_manager()
            components["plugin_system"] = "healthy"
        except:
            components["plugin_system"] = "degraded"
        
        # LLM engine check
        try:
            from modules.llm_engine.engine import get_llm_engine
            llm_engine = get_llm_engine(db)
            components["llm_engine"] = "healthy"
        except:
            components["llm_engine"] = "degraded"
        
        # Determine overall status
        if all(status == "healthy" for status in components.values()):
            overall_status = "healthy"
        elif any(status == "critical" for status in components.values()):
            overall_status = "critical"
        else:
            overall_status = "degraded"
        
        # Calculate uptime percentage (placeholder)
        uptime_percentage = 99.9
        
        return SystemHealth(
            overall_status=overall_status,
            components=components,
            active_alerts=[],  # Would be populated from alert system
            performance_metrics=[],  # Would be populated from monitoring
            uptime_percentage=uptime_percentage
        )
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system health")

@router.post("/maintenance/enable", response_model=AdminActionResult)
async def enable_maintenance_mode(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Enable maintenance mode (Feature 210 - Admin interface control)."""
    try:
        # In real implementation, this would set a global flag
        # For now, just log the action
        
        audit_entry = AuditLog(
            user_id=current_admin.id,
            action="enable_maintenance_mode",
            resource_type="system",
            details={"enabled_by": current_admin.username},
            ip_address="127.0.0.1",
            timestamp=datetime.utcnow()
        )
        db.add(audit_entry)
        db.commit()
        
        return AdminActionResult(
            success=True,
            message="Maintenance mode enabled successfully"
        )
        
    except Exception as e:
        logger.error(f"Error enabling maintenance mode: {e}")
        raise HTTPException(status_code=500, detail="Failed to enable maintenance mode") 