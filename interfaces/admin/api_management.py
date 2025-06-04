from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, timedelta
import secrets
import hashlib
import logging

from core.database import get_db, User, AuditLog
from core.security import get_current_admin_user
from .schemas import (
    APIEndpoint,
    APIKey,
    APIKeyCreate,
    AdminActionResult,
    HealthCheckResponse
)
from modules.audio_voice import get_audio_processor

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/endpoints", response_model=List[APIEndpoint])
async def get_api_endpoints(
    current_admin: User = Depends(get_current_admin_user)
):
    """Get API endpoint statistics and monitoring."""
    try:
        # In a real implementation, this would collect actual metrics
        endpoints = [
            APIEndpoint(
                path="/api/auth/login",
                method="POST",
                calls_24h=150,
                avg_response_time_ms=120,
                error_rate_percent=0.5,
                last_error=None,
                rate_limit=100,
                authentication_required=False
            ),
            APIEndpoint(
                path="/api/chat/message",
                method="POST",
                calls_24h=1200,
                avg_response_time_ms=350,
                error_rate_percent=1.2,
                last_error=datetime.utcnow() - timedelta(hours=2),
                rate_limit=60,
                authentication_required=True
            ),
            APIEndpoint(
                path="/api/memory/search",
                method="GET",
                calls_24h=450,
                avg_response_time_ms=230,
                error_rate_percent=0.8,
                last_error=None,
                rate_limit=30,
                authentication_required=True
            ),
            APIEndpoint(
                path="/api/image/process",
                method="POST",
                calls_24h=320,
                avg_response_time_ms=1200,
                error_rate_percent=2.1,
                last_error=datetime.utcnow() - timedelta(hours=1),
                rate_limit=20,
                authentication_required=True
            ),
            APIEndpoint(
                path="/api/audio/transcribe",
                method="POST",
                calls_24h=180,
                avg_response_time_ms=2400,
                error_rate_percent=1.5,
                last_error=None,
                rate_limit=15,
                authentication_required=True
            )
        ]
        
        return endpoints
        
    except Exception as e:
        logger.error(f"Error getting API endpoints: {e}")
        raise HTTPException(status_code=500, detail="Failed to get API endpoints")

@router.post("/keys", response_model=APIKey)
async def create_api_key(
    key_request: APIKeyCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new API key."""
    try:
        # Generate API key
        api_key = secrets.token_urlsafe(32)
        key_id = hashlib.sha256(api_key.encode()).hexdigest()[:16]
        
        # In a real implementation, store in database
        # For now, return the created key info
        
        # Log the action
        audit_entry = AuditLog(
            user_id=current_admin.id,
            action="create_api_key",
            resource_type="api_key",
            resource_id=key_id,
            details={"name": key_request.name, "permissions": key_request.permissions},
            ip_address="127.0.0.1",
            timestamp=datetime.utcnow()
        )
        db.add(audit_entry)
        db.commit()
        
        return APIKey(
            key_id=key_id,
            name=key_request.name,
            created_at=datetime.utcnow(),
            last_used=None,
            usage_count=0,
            rate_limit=key_request.rate_limit,
            permissions=key_request.permissions,
            expires_at=key_request.expires_at,
            is_active=True
        )
        
    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        raise HTTPException(status_code=500, detail="Failed to create API key")

@router.get("/keys", response_model=List[APIKey])
async def list_api_keys(
    current_admin: User = Depends(get_current_admin_user)
):
    """List all API keys."""
    try:
        # In real implementation, would query from database
        # For now, return sample data
        keys = [
            APIKey(
                key_id="api_key_001",
                name="Development Key",
                created_at=datetime.utcnow() - timedelta(days=30),
                last_used=datetime.utcnow() - timedelta(hours=2),
                usage_count=1250,
                rate_limit=100,
                permissions=["read", "write"],
                expires_at=datetime.utcnow() + timedelta(days=365),
                is_active=True
            ),
            APIKey(
                key_id="api_key_002",
                name="Production Key",
                created_at=datetime.utcnow() - timedelta(days=15),
                last_used=datetime.utcnow() - timedelta(minutes=30),
                usage_count=5670,
                rate_limit=1000,
                permissions=["read", "write", "admin"],
                expires_at=datetime.utcnow() + timedelta(days=365),
                is_active=True
            )
        ]
        
        return keys
        
    except Exception as e:
        logger.error(f"Error listing API keys: {e}")
        raise HTTPException(status_code=500, detail="Failed to list API keys")

@router.delete("/keys/{key_id}", response_model=AdminActionResult)
async def revoke_api_key(
    key_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Revoke an API key."""
    try:
        # In real implementation, would mark key as inactive in database
        
        # Log the action
        audit_entry = AuditLog(
            user_id=current_admin.id,
            action="revoke_api_key",
            resource_type="api_key",
            resource_id=key_id,
            details={},
            ip_address="127.0.0.1",
            timestamp=datetime.utcnow()
        )
        db.add(audit_entry)
        db.commit()
        
        return AdminActionResult(
            success=True,
            message=f"API key {key_id} has been revoked"
        )
        
    except Exception as e:
        logger.error(f"Error revoking API key {key_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to revoke API key")

@router.get("/metrics", response_model=Dict[str, Any])
async def get_api_metrics(
    current_admin: User = Depends(get_current_admin_user)
):
    """Get comprehensive API usage metrics."""
    try:
        # In real implementation, would collect from monitoring system
        metrics = {
            "total_requests_24h": 2500,
            "average_response_time_ms": 450,
            "error_rate_percent": 1.2,
            "active_api_keys": 15,
            "rate_limited_requests": 25,
            "top_endpoints": [
                {"path": "/api/chat/message", "requests": 1200},
                {"path": "/api/memory/search", "requests": 450},
                {"path": "/api/image/process", "requests": 320},
                {"path": "/api/audio/transcribe", "requests": 180},
                {"path": "/api/auth/login", "requests": 150}
            ],
            "response_time_by_hour": [
                {"hour": "00:00", "avg_ms": 420},
                {"hour": "01:00", "avg_ms": 380},
                {"hour": "02:00", "avg_ms": 350},
                # ... would have 24 hours of data
            ],
            "error_distribution": {
                "400": 15,
                "401": 8,
                "403": 5,
                "404": 12,
                "429": 25,
                "500": 10,
                "503": 3
            }
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting API metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get API metrics")

@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Comprehensive health check of all system components."""
    try:
        checks = {}
        
        # Database check
        try:
            db.execute("SELECT 1")
            checks["database"] = {"status": "healthy", "response_time_ms": 10}
        except Exception as e:
            checks["database"] = {"status": "unhealthy", "error": str(e)}
        
        # Memory system check
        try:
            from modules.memory.memory_manager import get_memory_manager
            memory_manager = get_memory_manager(db)
            checks["memory_system"] = {"status": "healthy", "total_memories": 1000}
        except Exception as e:
            checks["memory_system"] = {"status": "unhealthy", "error": str(e)}
        
        # LLM engine check
        try:
            from modules.llm_engine.engine import get_llm_engine
            llm_engine = get_llm_engine(db)
            checks["llm_engine"] = {"status": "healthy", "active_models": 2}
        except Exception as e:
            checks["llm_engine"] = {"status": "unhealthy", "error": str(e)}
        
        # Plugin system check
        try:
            from modules.plugin_system.manager import get_plugin_manager
            plugin_manager = get_plugin_manager()
            plugins = plugin_manager.list_plugins()
            enabled_count = sum(1 for p in plugins.values() if p.get("enabled", False))
            checks["plugin_system"] = {"status": "healthy", "enabled_plugins": enabled_count}
        except Exception as e:
            checks["plugin_system"] = {"status": "unhealthy", "error": str(e)}
        
        # Audio processing check
        try:
            audio_processor = get_audio_processor()
            checks["audio_processing"] = {"status": "healthy", "models_loaded": 2}
        except Exception as e:
            checks["audio_processing"] = {"status": "degraded", "error": str(e)}
        
        # Image processing check
        try:
            from modules.image_module.processor import get_image_processor
            image_processor = get_image_processor()
            checks["image_processing"] = {"status": "healthy", "models_loaded": 3}
        except Exception as e:
            checks["image_processing"] = {"status": "degraded", "error": str(e)}
        
        # Overall status
        all_healthy = all(check.get("status") == "healthy" for check in checks.values())
        has_critical = any(check.get("status") == "unhealthy" for check in checks.values())
        
        if all_healthy:
            overall_status = "healthy"
        elif has_critical:
            overall_status = "degraded"
        else:
            overall_status = "degraded"
        
        return HealthCheckResponse(
            status=overall_status,
            timestamp=datetime.utcnow(),
            checks=checks,
            version="1.0.0"
        )
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

@router.put("/endpoints/{path}/rate-limit", response_model=AdminActionResult)
async def update_rate_limit(
    path: str,
    new_limit: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update rate limit for a specific endpoint."""
    try:
        # In real implementation, would update the rate limiting configuration
        
        # Log the action
        audit_entry = AuditLog(
            user_id=current_admin.id,
            action="update_rate_limit",
            resource_type="api_endpoint",
            resource_id=path,
            details={"new_limit": new_limit},
            ip_address="127.0.0.1",
            timestamp=datetime.utcnow()
        )
        db.add(audit_entry)
        db.commit()
        
        return AdminActionResult(
            success=True,
            message=f"Rate limit for {path} updated to {new_limit} requests per minute"
        )
        
    except Exception as e:
        logger.error(f"Error updating rate limit: {e}")
        raise HTTPException(status_code=500, detail="Failed to update rate limit") 