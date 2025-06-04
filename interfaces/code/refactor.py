from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db, User
from core.security import get_current_active_user
from modules.code_analysis.analyzer import get_code_analyzer
from .schemas import CodeRefactorRequest, CodeRefactorResult

refactor_router = APIRouter()

@refactor_router.post("/refactor", response_model=CodeRefactorResult)
async def suggest_refactoring(
    request: CodeRefactorRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Suggest and perform code refactoring. (Features: 41, 103, 110, 115, 116, 117, 118, 204, 205)"""
    analyzer = get_code_analyzer()
    try:
        refactor_result = await analyzer.suggest_refactor(request.filename, request.content, request.options)
        return CodeRefactorResult(**refactor_result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Refactor failed: {str(e)}") 