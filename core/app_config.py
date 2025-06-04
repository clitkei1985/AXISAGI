from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging
from datetime import datetime

from .app_lifecycle import lifespan

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    # Create FastAPI app
    app = FastAPI(
        title="Axis AI",
        description="Advanced AI Assistant with Persistent Memory and Comprehensive Features",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure this appropriately in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Trusted host middleware for security
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure appropriately for production
    )

    # Mount static files
    static_path = Path(__file__).parent.parent / "modules" / "frontend_ui" / "static"
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    
    # Add request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log all HTTP requests."""
        start_time = datetime.utcnow()
        response = await call_next(request)
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info(
            f"{request.method} {request.url.path} "
            f"- {response.status_code} - {duration:.3f}s"
        )
        
        return response
    
    return app 