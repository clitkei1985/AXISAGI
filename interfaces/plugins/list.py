from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db, User
from core.security import get_current_active_user
from modules.plugin_system.manager import get_plugin_manager
from .schemas import PluginInfo, PluginListResponse, PluginStatus

list_router = APIRouter()

@list_router.get("/", response_model=PluginListResponse)
async def list_plugins(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all available plugins. (Features: 56, 57, 194, 204, 212)"""
    manager = get_plugin_manager()
    plugins_dict = manager.list_plugins()
    enabled_count = sum(1 for p in plugins_dict.values() if p["enabled"])
    disabled_count = len(plugins_dict) - enabled_count
    return PluginListResponse(
        plugins={name: PluginInfo(**info) for name, info in plugins_dict.items()},
        total_count=len(plugins_dict),
        enabled_count=enabled_count,
        disabled_count=disabled_count
    )

@list_router.get("/{plugin_name}", response_model=PluginInfo)
async def get_plugin_info(
    plugin_name: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific plugin. (Features: 56, 57, 194, 204, 212)"""
    manager = get_plugin_manager()
    info = manager.get_plugin_info(plugin_name)
    if not info:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return PluginInfo(**info)

@list_router.get("/{plugin_name}/status", response_model=PluginStatus)
async def get_plugin_status(
    plugin_name: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get the status of a specific plugin. (Features: 56, 57, 194, 204, 212)"""
    manager = get_plugin_manager()
    status = manager.get_plugin_status(plugin_name)
    if not status:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return PluginStatus(**status) 