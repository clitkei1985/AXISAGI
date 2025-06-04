from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def configure_exception_handlers(app: FastAPI):
    """Add global exception handlers to the FastAPI app"""
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler with logging. (Features: 120, 173, 174)"""
        logger.error(f"Global exception: {exc}", exc_info=True)
        
        # Log to analytics
        try:
            from modules.analytics_reporting.collector import log_error
            await log_error(
                error_type=type(exc).__name__,
                error_message=str(exc),
                request_path=str(request.url.path),
                request_method=request.method
            )
        except Exception as analytics_error:
            logger.error(f"Failed to log error to analytics: {analytics_error}")
        
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "timestamp": datetime.utcnow().isoformat()
            }
        ) 