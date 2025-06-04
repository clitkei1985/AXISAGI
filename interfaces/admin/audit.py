from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from core.database import get_db, User, AuditLog
from core.security import get_current_admin_user
from .schemas import (
    AuditLogEntry,
    AuditQuery,
    PaginatedResponse,
    AdminActionResult
)

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/logs", response_model=PaginatedResponse)
async def get_audit_logs(
    query: AuditQuery = Depends(),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get audit logs with filtering."""
    try:
        db_query = db.query(AuditLog).join(User)
        
        # Apply filters
        if query.user_id:
            db_query = db_query.filter(AuditLog.user_id == query.user_id)
        
        if query.action:
            db_query = db_query.filter(AuditLog.action.ilike(f"%{query.action}%"))
        
        if query.resource_type:
            db_query = db_query.filter(AuditLog.resource_type == query.resource_type)
        
        if query.start_time:
            db_query = db_query.filter(AuditLog.timestamp >= query.start_time)
        
        if query.end_time:
            db_query = db_query.filter(AuditLog.timestamp <= query.end_time)
        
        # Get total count
        total = db_query.count()
        
        # Apply pagination and ordering
        logs = db_query.order_by(AuditLog.timestamp.desc()).offset(query.offset).limit(query.limit).all()
        
        # Convert to response format
        audit_entries = []
        for log in logs:
            audit_entries.append(AuditLogEntry(
                id=log.id,
                timestamp=log.timestamp,
                user_id=log.user_id,
                username=log.user.username,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                details=log.details or {},
                ip_address=log.ip_address or "",
                user_agent=log.user_agent
            ))
        
        page = (query.offset // query.limit) + 1
        pages = (total + query.limit - 1) // query.limit
        
        return PaginatedResponse(
            items=audit_entries,
            total=total,
            page=page,
            per_page=query.limit,
            pages=pages
        )
        
    except Exception as e:
        logger.error(f"Error getting audit logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get audit logs")

@router.get("/console/live")
async def get_live_console(
    current_admin: User = Depends(get_current_admin_user)
):
    """Get real-time verbose console of backend operations (Feature 183)."""
    def generate_console_stream():
        """Generate live console output stream."""
        # This would integrate with the actual logging system
        # For now, return sample console output
        import time
        
        sample_logs = [
            "[INFO] System startup complete",
            "[DEBUG] Memory manager initialized",
            "[INFO] Plugin system loaded 5 plugins",
            "[WARNING] High memory usage detected: 85%",
            "[INFO] User authentication successful: admin",
            "[DEBUG] LLM engine processing request",
            "[INFO] Chat session created: session_123",
            "[DEBUG] Vector search completed in 0.23s",
            "[INFO] File upload processed successfully",
            "[WARNING] Rate limit approaching for user_456"
        ]
        
        for log in sample_logs:
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            yield f"data: [{timestamp}] {log}\n\n"
            time.sleep(1)
    
    return StreamingResponse(
        generate_console_stream(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

@router.get("/logs/export")
async def export_audit_logs(
    start_date: datetime = None,
    end_date: datetime = None,
    format: str = "csv",
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Export audit logs to file."""
    try:
        query = db.query(AuditLog).join(User)
        
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        
        logs = query.order_by(AuditLog.timestamp.desc()).all()
        
        # Generate export content
        if format.lower() == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                "Timestamp", "User", "Action", "Resource Type", 
                "Resource ID", "IP Address", "Details"
            ])
            
            # Write data
            for log in logs:
                writer.writerow([
                    log.timestamp.isoformat(),
                    log.user.username,
                    log.action,
                    log.resource_type,
                    log.resource_id or "",
                    log.ip_address or "",
                    str(log.details) if log.details else ""
                ])
            
            content = output.getvalue()
            output.close()
            
            return StreamingResponse(
                io.StringIO(content),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=audit_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"}
            )
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported export format")
        
    except Exception as e:
        logger.error(f"Error exporting audit logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to export audit logs")

@router.delete("/logs/cleanup", response_model=AdminActionResult)
async def cleanup_old_logs(
    days_to_keep: int = 90,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Clean up old audit logs."""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Count logs to be deleted
        count = db.query(AuditLog).filter(AuditLog.timestamp < cutoff_date).count()
        
        # Delete old logs
        db.query(AuditLog).filter(AuditLog.timestamp < cutoff_date).delete()
        db.commit()
        
        # Log the cleanup action
        audit_entry = AuditLog(
            user_id=current_admin.id,
            action="cleanup_audit_logs",
            resource_type="audit_log",
            details={"days_to_keep": days_to_keep, "deleted_count": count},
            ip_address="127.0.0.1",
            timestamp=datetime.utcnow()
        )
        db.add(audit_entry)
        db.commit()
        
        return AdminActionResult(
            success=True,
            message=f"Cleaned up {count} old audit log entries",
            affected_count=count
        )
        
    except Exception as e:
        logger.error(f"Error cleaning up audit logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup audit logs")

@router.get("/rules/view")
async def view_ai_rules(
    current_admin: User = Depends(get_current_admin_user)
):
    """View all AI governance rules (Feature 210)."""
    try:
        # In real implementation, this would read from a rules database
        rules = {
            "core_rules": {
                "rule_001": {
                    "description": "Never override or modify own rules",
                    "locked": True,
                    "priority": "critical"
                },
                "rule_002": {
                    "description": "Require user approval for plugin deployment",
                    "locked": True,
                    "priority": "high"
                },
                "rule_003": {
                    "description": "Maintain audit trail of all actions",
                    "locked": False,
                    "priority": "high"
                }
            },
            "plugin_rules": {
                "rule_101": {
                    "description": "Sandbox test all generated plugins",
                    "locked": True,
                    "priority": "critical"
                }
            },
            "security_rules": {
                "rule_201": {
                    "description": "Encrypt sensitive data at rest",
                    "locked": False,
                    "priority": "high"
                }
            }
        }
        
        return {
            "success": True,
            "rules": rules,
            "total_rules": sum(len(category) for category in rules.values()),
            "locked_rules": sum(
                sum(1 for rule in category.values() if rule.get("locked", False))
                for category in rules.values()
            )
        }
        
    except Exception as e:
        logger.error(f"Error viewing AI rules: {e}")
        raise HTTPException(status_code=500, detail="Failed to view AI rules") 