from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from core.database import get_db, User
from core.security import get_current_user
from modules.system.live_reloader import get_reloader, start_live_reloading, stop_live_reloading

router = APIRouter(prefix="/reload", tags=["live-reloading"])

@router.post("/start")
async def start_reload_monitoring(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start live module reloading"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    reloader = start_live_reloading()
    return {"message": "Live reloading started", "monitoring": reloader.is_monitoring}

@router.post("/stop")
async def stop_reload_monitoring(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stop live module reloading"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    stop_live_reloading()
    return {"message": "Live reloading stopped"}

@router.post("/manual/{module_path}")
async def reload_module_manually(
    module_path: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually reload a specific module"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    reloader = get_reloader()
    success = reloader.reload_module(module_path)
    
    if success:
        return {"message": f"Module {module_path} reloaded successfully"}
    else:
        raise HTTPException(status_code=400, detail=f"Failed to reload {module_path}")

@router.get("/status")
async def get_reload_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get live reloading status"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    reloader = get_reloader()
    return {
        "monitoring": reloader.is_monitoring,
        "watched_modules": len(reloader.watched_modules),
        "callback_count": len(reloader.reload_callbacks)
    } 