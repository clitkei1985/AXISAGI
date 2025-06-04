from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from core.database import get_db, User
from core.security import get_current_admin_user
from modules.plugin_system.manager import get_plugin_manager
from .schemas import PluginConfig, PluginInstallRequest, PluginInstallResponse
import base64

manage_router = APIRouter()

@manage_router.post("/load")
async def load_plugins(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Load all plugins from the plugins directory. (Features: 56, 57, 194, 204, 212)"""
    manager = get_plugin_manager()
    results = await manager.load_all_plugins()
    return {
        "loaded_plugins": results,
        "total_loaded": sum(1 for success in results.values() if success),
        "total_failed": sum(1 for success in results.values() if not success)
    }

@manage_router.post("/{plugin_name}/enable")
async def enable_plugin(
    plugin_name: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Enable a specific plugin. (Features: 56, 57, 194, 204, 212)"""
    manager = get_plugin_manager()
    success = await manager.enable_plugin(plugin_name)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to enable plugin")
    return {"detail": f"Plugin {plugin_name} enabled successfully"}

@manage_router.post("/{plugin_name}/disable")
async def disable_plugin(
    plugin_name: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Disable a specific plugin. (Features: 56, 57, 194, 204, 212)"""
    manager = get_plugin_manager()
    success = await manager.disable_plugin(plugin_name)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to disable plugin")
    return {"detail": f"Plugin {plugin_name} disabled successfully"}

@manage_router.delete("/{plugin_name}")
async def unload_plugin(
    plugin_name: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Unload a specific plugin. (Features: 56, 57, 194, 204, 212)"""
    manager = get_plugin_manager()
    success = await manager.unload_plugin(plugin_name)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to unload plugin")
    return {"detail": f"Plugin {plugin_name} unloaded successfully"}

@manage_router.put("/{plugin_name}/config")
async def update_plugin_config(
    plugin_name: str,
    config: PluginConfig,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update plugin configuration. (Features: 56, 57, 194, 204, 212)"""
    manager = get_plugin_manager()
    success = await manager.update_plugin_config(plugin_name, config.config)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update plugin configuration")
    return {"detail": f"Plugin {plugin_name} configuration updated successfully"}

@manage_router.post("/install", response_model=PluginInstallResponse)
async def install_plugin(
    request: PluginInstallRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Install a new plugin from URL or uploaded data. (Features: 56, 57, 194, 204, 205, 206, 207, 212)"""
    try:
        plugin_data = None
        if request.plugin_url:
            import requests
            response = requests.get(request.plugin_url)
            response.raise_for_status()
            plugin_data = response.content
        elif request.plugin_data:
            plugin_data = base64.b64decode(request.plugin_data)
        else:
            raise HTTPException(status_code=400, detail="Either plugin_url or plugin_data must be provided")
        # Save plugin file (implementation depends on manager)
        manager = get_plugin_manager()
        result = await manager.install_plugin(plugin_data)
        return PluginInstallResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Plugin install failed: {str(e)}")

@manage_router.post("/upload", response_model=PluginInstallResponse)
async def upload_plugin(
    file: UploadFile = File(...),
    auto_enable: bool = False,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Upload a plugin file. (Features: 56, 57, 194, 204, 205, 206, 207, 212)"""
    try:
        plugin_data = await file.read()
        manager = get_plugin_manager()
        result = await manager.install_plugin(plugin_data, auto_enable=auto_enable)
        return PluginInstallResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Plugin upload failed: {str(e)}") 