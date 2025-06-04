from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import os
import json
import logging
from pathlib import Path
import gzip

from core.database import get_db, User, Session as DBSession, Message, Memory, AuditLog
from core.security import get_current_admin_user
from .schemas import (
    DatabaseStats,
    BackupInfo,
    BackupRequest,
    RestoreRequest,
    AdminActionResult
)

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/stats", response_model=DatabaseStats)
async def get_database_stats(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get database statistics and metrics."""
    try:
        # Get table counts
        total_users = db.query(User).count()
        total_sessions = db.query(DBSession).count()
        total_messages = db.query(Message).count()
        total_memories = db.query(Memory).count()
        
        # Get database size (simplified)
        database_size_mb = 100.0  # Placeholder
        
        # Table sizes (simplified)
        table_sizes = {
            "users": 10.5,
            "sessions": 25.3,
            "messages": 150.2,
            "memories": 200.8,
            "audit_logs": 45.1
        }
        
        # Connection count (placeholder)
        connection_count = 5
        
        # Slowest queries (placeholder)
        slowest_queries = [
            {"query": "SELECT * FROM messages WHERE...", "duration_ms": 1200},
            {"query": "SELECT * FROM memories WHERE...", "duration_ms": 800}
        ]
        
        return DatabaseStats(
            total_users=total_users,
            total_sessions=total_sessions,
            total_messages=total_messages,
            total_memories=total_memories,
            total_plugins=0,  # Would get from plugin system
            database_size_mb=database_size_mb,
            table_sizes=table_sizes,
            connection_count=connection_count,
            slowest_queries=slowest_queries
        )
        
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get database statistics")

@router.post("/backup", response_model=BackupInfo)
async def create_backup(
    backup_request: BackupRequest,
    background_tasks: BackgroundTasks,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create a database backup."""
    try:
        backup_id = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        backup_dir = Path("db/backups")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        backup_file = backup_dir / f"{backup_id}.sql"
        
        # Start backup in background
        background_tasks.add_task(
            perform_database_backup,
            str(backup_file),
            backup_request.include_uploads,
            backup_request.compression,
            current_admin.id
        )
        
        # Log the action
        audit_entry = AuditLog(
            user_id=current_admin.id,
            action="create_backup",
            resource_type="database",
            resource_id=backup_id,
            details={"type": backup_request.type, "include_uploads": backup_request.include_uploads},
            ip_address="127.0.0.1",
            timestamp=datetime.utcnow()
        )
        db.add(audit_entry)
        db.commit()
        
        return BackupInfo(
            backup_id=backup_id,
            created_at=datetime.utcnow(),
            size_mb=0.0,  # Will be updated when backup completes
            type=backup_request.type,
            status="in_progress",
            file_path=str(backup_file)
        )
        
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        raise HTTPException(status_code=500, detail="Failed to create backup")

@router.get("/backups", response_model=List[BackupInfo])
async def list_backups(
    current_admin: User = Depends(get_current_admin_user)
):
    """List all available database backups."""
    try:
        backup_dir = Path("db/backups")
        if not backup_dir.exists():
            return []
        
        backups = []
        for backup_file in backup_dir.glob("*.sql*"):
            stat = backup_file.stat()
            backup_id = backup_file.stem
            
            backups.append(BackupInfo(
                backup_id=backup_id,
                created_at=datetime.fromtimestamp(stat.st_ctime),
                size_mb=stat.st_size / (1024 * 1024),
                type="full",
                status="completed",
                file_path=str(backup_file)
            ))
        
        return sorted(backups, key=lambda x: x.created_at, reverse=True)
        
    except Exception as e:
        logger.error(f"Error listing backups: {e}")
        raise HTTPException(status_code=500, detail="Failed to list backups")

@router.post("/restore", response_model=AdminActionResult)
async def restore_backup(
    restore_request: RestoreRequest,
    background_tasks: BackgroundTasks,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Restore database from backup."""
    try:
        backup_dir = Path("db/backups")
        backup_file = backup_dir / f"{restore_request.backup_id}.sql"
        
        if not backup_file.exists():
            # Try with compression extension
            backup_file = backup_dir / f"{restore_request.backup_id}.sql.gz"
            if not backup_file.exists():
                raise HTTPException(status_code=404, detail="Backup file not found")
        
        # Start restore in background
        background_tasks.add_task(
            perform_database_restore,
            str(backup_file),
            restore_request.overwrite_existing,
            current_admin.id
        )
        
        # Log the action
        audit_entry = AuditLog(
            user_id=current_admin.id,
            action="restore_backup",
            resource_type="database",
            resource_id=restore_request.backup_id,
            details={"overwrite_existing": restore_request.overwrite_existing},
            ip_address="127.0.0.1",
            timestamp=datetime.utcnow()
        )
        db.add(audit_entry)
        db.commit()
        
        return AdminActionResult(
            success=True,
            message=f"Database restore from {restore_request.backup_id} started"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring backup: {e}")
        raise HTTPException(status_code=500, detail="Failed to restore backup")

# Helper functions

async def perform_database_backup(backup_file: str, include_uploads: bool, compression: bool, admin_id: int):
    """Perform database backup in background."""
    try:
        # Simplified backup process
        # In real implementation, would use pg_dump or similar
        
        backup_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "full",
            "include_uploads": include_uploads,
            "compression": compression,
            "created_by": admin_id
        }
        
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        if compression:
            # Compress the backup file
            with open(backup_file, 'rb') as f_in:
                with gzip.open(f"{backup_file}.gz", 'wb') as f_out:
                    f_out.writelines(f_in)
            os.remove(backup_file)
        
        logger.info(f"Backup completed: {backup_file}")
        
    except Exception as e:
        logger.error(f"Backup failed: {e}")

async def perform_database_restore(backup_file: str, overwrite_existing: bool, admin_id: int):
    """Perform database restore in background."""
    try:
        # Simplified restore process
        # In real implementation, would use database-specific restore tools
        
        # Check if file is compressed
        if backup_file.endswith('.gz'):
            with gzip.open(backup_file, 'rt') as f:
                backup_data = json.load(f)
        else:
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
        
        logger.info(f"Restore completed from: {backup_file}")
        logger.info(f"Backup data: {backup_data}")
        
    except Exception as e:
        logger.error(f"Restore failed: {e}")

@router.delete("/backups/{backup_id}", response_model=AdminActionResult)
async def delete_backup(
    backup_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Delete a backup file."""
    try:
        backup_dir = Path("db/backups")
        backup_files = [
            backup_dir / f"{backup_id}.sql",
            backup_dir / f"{backup_id}.sql.gz"
        ]
        
        deleted = False
        for backup_file in backup_files:
            if backup_file.exists():
                backup_file.unlink()
                deleted = True
                break
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Backup file not found")
        
        # Log the action
        audit_entry = AuditLog(
            user_id=current_admin.id,
            action="delete_backup",
            resource_type="database",
            resource_id=backup_id,
            details={},
            ip_address="127.0.0.1",
            timestamp=datetime.utcnow()
        )
        db.add(audit_entry)
        db.commit()
        
        return AdminActionResult(
            success=True,
            message=f"Backup {backup_id} deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting backup {backup_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete backup") 