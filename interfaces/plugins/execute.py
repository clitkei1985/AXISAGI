from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db, User
from core.security import get_current_active_user
from modules.plugin_system.manager import get_plugin_manager
from .schemas import PluginAction, PluginActionResult
import time

execute_router = APIRouter()

@execute_router.post("/{plugin_name}/execute", response_model=PluginActionResult)
async def execute_plugin_action(
    plugin_name: str,
    action: PluginAction,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Execute an action on a specific plugin. (Features: 56, 57, 58, 164, 194, 204, 205, 206, 207, 212)"""
    manager = get_plugin_manager()
    start_time = time.time()
    try:
        result = await manager.execute_plugin_action(
            plugin_name,
            action.action,
            user=current_user,
            **action.parameters
        )
        execution_time = time.time() - start_time
        return PluginActionResult(
            success=True,
            result=result,
            execution_time=execution_time
        )
    except Exception as e:
        execution_time = time.time() - start_time
        return PluginActionResult(
            success=False,
            error=str(e),
            execution_time=execution_time
        ) 