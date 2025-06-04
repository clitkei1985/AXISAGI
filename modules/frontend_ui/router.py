from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from core.security import get_current_user_optional
from core.database import get_db, User
from sqlalchemy.orm import Session

# Setup templates
template_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(template_dir))

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    db: Session = Depends(get_db)
):
    """Serve main application interface. (Features: 36, 38, 40, 41, 48, 49)"""
    # Always serve the main page - let JavaScript handle authentication
    return templates.TemplateResponse("index.html", {
        "request": request
    })

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Serve login page. (Features: 36, 128)"""
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/admin", response_class=HTMLResponse)
async def admin_page(
    request: Request,
    current_user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Serve admin interface. (Features: 120, 121, 122, 123, 124, 125, 126, 127, 134, 135, 136, 210)"""
    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "user": current_user
    })

@router.get("/analytics", response_class=HTMLResponse)  
async def analytics_page(
    request: Request,
    current_user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Serve analytics dashboard. (Features: 29, 31, 59, 120, 122, 123, 124, 134, 200)"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    return templates.TemplateResponse("analytics.html", {
        "request": request,
        "user": current_user
    })

@router.get("/plugins", response_class=HTMLResponse)
async def plugins_page(
    request: Request,
    current_user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Serve plugin management interface. (Features: 56, 57, 194, 204, 205, 206, 207, 212)"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    return templates.TemplateResponse("plugins.html", {
        "request": request,
        "user": current_user
    })
