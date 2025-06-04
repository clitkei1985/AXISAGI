from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import psutil
import os
import json
import logging
from pathlib import Path
import zipfile
import tempfile
import hashlib
import secrets

from core.database import get_db, User, Session as DBSession, Message, Memory, AuditLog
from core.security import get_current_admin_user, create_access_token, get_password_hash
from modules.analytics_reporting.analytics import get_analytics_collector
from modules.plugin_system.manager import get_plugin_manager
from .schemas import (
    SystemStatus,
    SystemConfig,
    SystemConfigUpdate,
    UserInfo,
    UserCreate,
    UserUpdate,
    BulkUserAction,
    DatabaseStats,
    BackupInfo,
    BackupRequest,
    RestoreRequest,
    PluginInfo,
    LogEntry,
    LogQuery,
    LogStats,
    AlertRule,
    Alert,
    SystemHealth,
    MaintenanceWindow,
    SecurityEvent,
    SecurityRule,
    AuditLogEntry,
    AuditQuery,
    PerformanceMetrics,
    APIEndpoint,
    APIKey,
    APIKeyCreate,
    AdminActionResult,
    PaginatedResponse,
    HealthCheckResponse
)
from . import system, users, database, audit, api_management

logger = logging.getLogger(__name__)
router = APIRouter()

# Include sub-routers for different admin functionality
router.include_router(system.router, prefix="/system", tags=["System Management"])
router.include_router(users.router, prefix="/users", tags=["User Management"])
router.include_router(database.router, prefix="/database", tags=["Database Management"])
router.include_router(audit.router, prefix="/audit", tags=["Audit & Logging"])
router.include_router(api_management.router, prefix="/api", tags=["API Management"])

# Plugin Management Endpoints (keeping these in main router for now)

@router.get("/plugins/", response_model=List[PluginInfo])
async def list_plugins(
    current_admin: User = Depends(get_current_admin_user)
):
    """List all installed plugins."""
    try:
        plugin_manager = get_plugin_manager()
        plugins = plugin_manager.list_plugins()
        
        plugin_infos = []
        for plugin_id, plugin_data in plugins.items():
            plugin_infos.append(PluginInfo(
                plugin_id=plugin_id,
                name=plugin_data.get("name", plugin_id),
                version=plugin_data.get("version", "1.0.0"),
                description=plugin_data.get("description", ""),
                author=plugin_data.get("author", "Unknown"),
                enabled=plugin_data.get("enabled", False),
                installed_at=datetime.utcnow(),  # Would be stored in plugin metadata
                last_updated=None,
                dependencies=plugin_data.get("dependencies", []),
                permissions=plugin_data.get("permissions", []),
                file_size_mb=0.0  # Would calculate actual size
            ))
        
        return plugin_infos
        
    except Exception as e:
        logger.error(f"Error listing plugins: {e}")
        raise HTTPException(status_code=500, detail="Failed to list plugins")

@router.post("/plugins/{plugin_id}/enable", response_model=AdminActionResult)
async def enable_plugin(
    plugin_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Enable a plugin."""
    try:
        plugin_manager = get_plugin_manager()
        result = plugin_manager.enable_plugin(plugin_id)
        
        if result:
            # Log the action
            from core.database import AuditLog
            from datetime import datetime
            
            audit_entry = AuditLog(
                user_id=current_admin.id,
                action="enable_plugin",
                resource_type="plugin",
                resource_id=plugin_id,
                details={},
                ip_address="127.0.0.1",
                timestamp=datetime.utcnow()
            )
            db.add(audit_entry)
            db.commit()
            
            return AdminActionResult(
                success=True,
                message=f"Plugin {plugin_id} enabled successfully"
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to enable plugin")
        
    except Exception as e:
        logger.error(f"Error enabling plugin {plugin_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to enable plugin")

@router.post("/plugins/{plugin_id}/disable", response_model=AdminActionResult)
async def disable_plugin(
    plugin_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Disable a plugin."""
    try:
        plugin_manager = get_plugin_manager()
        result = plugin_manager.disable_plugin(plugin_id)
        
        if result:
            # Log the action
            from core.database import AuditLog
            from datetime import datetime
            
            audit_entry = AuditLog(
                user_id=current_admin.id,
                action="disable_plugin",
                resource_type="plugin",
                resource_id=plugin_id,
                details={},
                ip_address="127.0.0.1",
                timestamp=datetime.utcnow()
            )
            db.add(audit_entry)
            db.commit()
            
            return AdminActionResult(
                success=True,
                message=f"Plugin {plugin_id} disabled successfully"
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to disable plugin")
        
    except Exception as e:
        logger.error(f"Error disabling plugin {plugin_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to disable plugin")

@router.delete("/plugins/{plugin_id}", response_model=AdminActionResult)
async def uninstall_plugin(
    plugin_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Uninstall a plugin."""
    try:
        plugin_manager = get_plugin_manager()
        result = plugin_manager.uninstall_plugin(plugin_id)
        
        if result:
            # Log the action
            from core.database import AuditLog
            from datetime import datetime
            
            audit_entry = AuditLog(
                user_id=current_admin.id,
                action="uninstall_plugin",
                resource_type="plugin",
                resource_id=plugin_id,
                details={},
                ip_address="127.0.0.1",
                timestamp=datetime.utcnow()
            )
            db.add(audit_entry)
            db.commit()
            
            return AdminActionResult(
                success=True,
                message=f"Plugin {plugin_id} uninstalled successfully"
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to uninstall plugin")
        
    except Exception as e:
        logger.error(f"Error uninstalling plugin {plugin_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to uninstall plugin")
