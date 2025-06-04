from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db, User
from core.security import get_current_active_user
from modules.code_analysis.analyzer import get_code_analyzer
from .schemas import CodeDuplicationRequest, DuplicationAnalysisResult

duplication_router = APIRouter()

@duplication_router.post("/duplication", response_model=DuplicationAnalysisResult)
async def analyze_duplication(
    request: CodeDuplicationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Analyze code for duplication and provide metrics. (Features: 41, 103, 110, 116, 117, 118, 204)"""
    analyzer = get_code_analyzer()
    try:
        result = await analyzer.analyze_duplication(request.filename, request.content)
        return DuplicationAnalysisResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Duplication analysis failed: {str(e)}") 