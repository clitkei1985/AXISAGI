from fastapi import FastAPI
import logging

logger = logging.getLogger(__name__)

def include_routers(app: FastAPI):
    """Include all routers in the FastAPI app"""
    from .route_config import configure_routers
    configure_routers(app)

def add_exception_handlers(app: FastAPI):
    """Add global exception handlers"""
    from .exception_handlers import configure_exception_handlers
    configure_exception_handlers(app)

def add_health_endpoints(app: FastAPI):
    """Add health check endpoints"""
    from .health_endpoints import configure_health_endpoints
    configure_health_endpoints(app) 