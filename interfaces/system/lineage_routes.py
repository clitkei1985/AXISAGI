from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from core.database import get_db, User
from core.security import get_current_user
from modules.analytics.lineage_tracker import get_lineage_tracker, SourceType
from .schemas import LineageStartRequest, LineageSourceRequest, ReasoningStepRequest, LineageFinalizeRequest

router = APIRouter(prefix="/lineage", tags=["lineage-tracking"])

@router.post("/start")
async def start_lineage_trace(
    request: LineageStartRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a new lineage trace"""
    tracker = get_lineage_tracker(db)
    trace_id = tracker.start_trace(
        request.query, 
        current_user.id, 
        request.session_id
    )
    
    return {"trace_id": trace_id, "query": request.query}

@router.post("/{trace_id}/source")
async def add_lineage_source(
    trace_id: str,
    request: LineageSourceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a source to lineage trace"""
    try:
        source_type = SourceType(request.source_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid source type: {request.source_type}")
    
    tracker = get_lineage_tracker(db)
    source_id = tracker.add_source(
        trace_id, 
        source_type, 
        request.description, 
        request.content,
        request.metadata,
        request.confidence
    )
    
    return {"source_id": source_id, "trace_id": trace_id}

@router.post("/{trace_id}/reasoning")
async def add_reasoning_step(
    trace_id: str,
    request: ReasoningStepRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a reasoning step to lineage trace"""
    tracker = get_lineage_tracker(db)
    step_id = tracker.add_reasoning_step(
        trace_id,
        request.step_type,
        request.input_sources,
        request.output_data,
        request.reasoning_text,
        request.confidence,
        request.model_used
    )
    
    return {"step_id": step_id, "trace_id": trace_id}

@router.post("/{trace_id}/finalize")
async def finalize_lineage_trace(
    trace_id: str,
    request: LineageFinalizeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Finalize lineage trace with final answer"""
    tracker = get_lineage_tracker(db)
    trace = tracker.finalize_trace(trace_id, request.final_answer)
    
    return {
        "trace_id": trace_id,
        "final_answer": request.final_answer,
        "sources_count": len(trace.sources),
        "reasoning_steps_count": len(trace.reasoning_steps)
    }

@router.get("/{trace_id}")
async def get_lineage_trace(
    trace_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed lineage information"""
    tracker = get_lineage_tracker(db)
    lineage = tracker.get_detailed_lineage(trace_id)
    
    if not lineage:
        raise HTTPException(status_code=404, detail="Lineage trace not found")
    
    return lineage

@router.get("/{trace_id}/validate")
async def validate_lineage_trace(
    trace_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate lineage trace completeness and consistency"""
    tracker = get_lineage_tracker(db)
    validation = tracker.validate_lineage(trace_id)
    
    return validation

@router.get("/{trace_id}/export")
async def export_lineage_trace(
    trace_id: str,
    format: str = "json",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export lineage trace in specified format"""
    tracker = get_lineage_tracker(db)
    
    try:
        exported_data = tracker.export_lineage(trace_id, format)
        return {"trace_id": trace_id, "format": format, "data": exported_data}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) 