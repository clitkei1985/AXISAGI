from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from core.database import get_db, User
from core.security import get_current_admin_user
from modules.plugin_system.manager import get_plugin_manager
from .schemas import HookRegistration

hooks_router = APIRouter()

@hooks_router.post("/hooks/register")
async def register_hook(
    hook: HookRegistration,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Register a new plugin hook. (Features: 56, 57, 58, 164, 194, 204, 205, 206, 207, 208, 212)"""
    manager = get_plugin_manager()
    success = await manager.register_hook(hook)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to register hook")
    return {"detail": f"Hook {hook.hook_name} registered successfully"}

@hooks_router.post("/hooks/{hook_name}/trigger")
async def trigger_hook(
    hook_name: str,
    parameters: Dict[str, Any] = {},
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Trigger a registered plugin hook. (Features: 56, 57, 58, 164, 194, 204, 205, 206, 207, 208, 212)"""
    manager = get_plugin_manager()
    result = await manager.trigger_hook(hook_name, parameters)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to trigger hook")
    return {"detail": f"Hook {hook_name} triggered successfully", "result": result} 