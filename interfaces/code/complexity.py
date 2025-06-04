from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db, User
from core.security import get_current_active_user
from modules.code_analysis.analyzer import get_code_analyzer
from .schemas import CodeComplexityRequest, ComplexityAnalysis

complexity_router = APIRouter()

@complexity_router.post("/complexity", response_model=ComplexityAnalysis)
async def analyze_complexity(
    request: CodeComplexityRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Analyze code complexity and provide metrics. (Features: 41, 103, 110, 116, 117, 118, 204)"""
    analyzer = get_code_analyzer()
    try:
        result = await analyzer.analyze_complexity(request.filename, request.content)
        return ComplexityAnalysis(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Complexity analysis failed: {str(e)}") 