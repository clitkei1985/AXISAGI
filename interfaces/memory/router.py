# interfaces/memory/router.py

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime

from core.database import get_db, User
from core.security import get_current_active_user
from modules.memory.memory_manager import get_memory_manager
from .schemas import (
    MemoryCreate,
    MemoryResponse,
    MemoryUpdate,
    MemorySearch,
    BatchMemoryCreate,
    MemoryStats
)

router = APIRouter()

@router.post("/", response_model=MemoryResponse)
async def create_memory(
    memory: MemoryCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new memory."""
    memory_manager = get_memory_manager(db)
    return memory_manager.add_memory(
        user=current_user,
        content=memory.content,
        metadata=memory.metadata,
        source=memory.source,
        privacy_level=memory.privacy_level,
        tags=memory.tags,
        project_id=memory.project_id
    )

@router.post("/batch", response_model=List[MemoryResponse])
async def create_memories_batch(
    memories: BatchMemoryCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create multiple memories in batch."""
    memory_manager = get_memory_manager(db)
    results = []
    
    for memory in memories.items:
        result = memory_manager.add_memory(
            user=current_user,
            content=memory.content,
            metadata=memory.metadata,
            source=memory.source,
            privacy_level=memory.privacy_level,
            tags=memory.tags,
            project_id=memory.project_id
        )
        results.append(result)
    
    return results

@router.get("/search", response_model=List[MemoryResponse])
async def search_memories(
    query: str = Query(..., min_length=1),
    k: int = Query(5, gt=0, le=100),
    privacy_levels: Optional[List[str]] = Query(None),
    project_id: Optional[int] = Query(None),
    min_similarity: float = Query(0.7, gt=0, le=1),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Search for memories using semantic similarity."""
    memory_manager = get_memory_manager(db)
    results = memory_manager.search_memories(
        query=query,
        user=current_user,
        k=k,
        privacy_levels=privacy_levels,
        project_id=project_id,
        min_similarity=min_similarity
    )
    return [memory for memory, _ in results]

@router.get("/stats", response_model=MemoryStats)
async def get_memory_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get memory statistics for the current user."""
    memory_manager = get_memory_manager(db)
    return memory_manager.get_stats(user=current_user)

@router.put("/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory_id: int,
    memory: MemoryUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an existing memory."""
    memory_manager = get_memory_manager(db)
    return memory_manager.update_memory(
        memory_id=memory_id,
        user=current_user,
        content=memory.content,
        metadata=memory.metadata,
        tags=memory.tags,
        privacy_level=memory.privacy_level
    )

@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a memory."""
    memory_manager = get_memory_manager(db)
    memory_manager.delete_memory(memory_id=memory_id, user=current_user)
    return {"detail": "Memory deleted"}

@router.post("/cleanup")
async def cleanup_memories(
    max_age_days: int = Query(30, gt=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Clean up old memories."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    memory_manager = get_memory_manager(db)
    memory_manager.cleanup_old_memories(max_age_days=max_age_days)
    return {"detail": "Memory cleanup completed"}

@router.post("/export")
async def export_memories(
    format: str = Query("json", pattern="^(json|csv)$"),
    privacy_levels: Optional[List[str]] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Export memories in specified format."""
    memory_manager = get_memory_manager(db)
    return memory_manager.export_memories(
        user=current_user,
        format=format,
        privacy_levels=privacy_levels
    )

@router.post("/import")
async def import_memories(
    import_data: str = Body(...),
    format: str = Query("json", pattern="^(json|csv)$"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Import memories from specified format."""
    memory_manager = get_memory_manager(db)
    imported = memory_manager.import_memories(
        user=current_user,
        import_data=import_data,
        format=format
    )
    return {"detail": f"Imported {len(imported)} memories"}

@router.get("/list", response_model=List[MemoryResponse])
async def list_memories(
    page: int = Query(1, gt=0),
    limit: int = Query(50, gt=0, le=1000),
    privacy_levels: Optional[List[str]] = Query(None),
    project_id: Optional[int] = Query(None),
    tags: Optional[List[str]] = Query(None),
    source: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List memories for the current user with pagination and filtering."""
    memory_manager = get_memory_manager(db)
    return memory_manager.list_memories(
        user=current_user,
        page=page,
        limit=limit,
        privacy_levels=privacy_levels,
        project_id=project_id,
        tags=tags,
        source=source
    )
