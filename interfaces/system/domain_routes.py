from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from sqlalchemy.orm import Session
from core.database import get_db, User
from core.security import get_current_user
from modules.ai.domain_switcher import get_domain_switcher, TaskDomain
from .schemas import ModelPerformanceRequest

router = APIRouter(prefix="/domain", tags=["domain-switching"])

@router.get("/detect")
async def detect_task_domain(
    prompt: str,
    context: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Detect task domain from prompt"""
    domain_switcher = get_domain_switcher(db)
    domain = domain_switcher.detect_task_domain(prompt, context)
    
    return {
        "detected_domain": domain.value,
        "prompt": prompt,
        "context": context
    }

@router.get("/models/{domain}")
async def get_best_model_for_domain(
    domain: str,
    preference: str = "balanced",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get best model for a specific domain"""
    try:
        domain_enum = TaskDomain(domain)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid domain: {domain}")
    
    domain_switcher = get_domain_switcher(db)
    model = domain_switcher.select_best_model(domain_enum, preference)
    
    return {
        "domain": domain,
        "preference": preference,
        "recommended_model": model
    }

@router.get("/recommendations")
async def get_model_recommendations(
    prompt: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get ranked model recommendations for a prompt"""
    domain_switcher = get_domain_switcher(db)
    recommendations = domain_switcher.get_model_recommendations(prompt)
    
    return {
        "prompt": prompt,
        "recommendations": [
            {
                "model": name,
                "score": score,
                "explanation": explanation
            }
            for name, score, explanation in recommendations
        ]
    }

@router.post("/performance")
async def record_model_performance(
    request: ModelPerformanceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record model performance for future selection"""
    try:
        domain_enum = TaskDomain(request.domain)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid domain: {request.domain}")
    
    domain_switcher = get_domain_switcher(db)
    domain_switcher.record_performance(
        request.model_name, 
        domain_enum, 
        request.performance_score
    )
    
    return {"message": "Performance recorded successfully"} 