from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db, User
from core.security import get_current_active_user
from modules.code_analysis.analyzer import get_code_analyzer
from .schemas import CodeSearchRequest, CodeSearchResult

search_router = APIRouter()

@search_router.post("/search", response_model=CodeSearchResult)
async def search_code(
    request: CodeSearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Search codebase for patterns, symbols, or text. (Features: 41, 103, 110, 116, 117, 118, 204)"""
    analyzer = get_code_analyzer()
    try:
        result = await analyzer.search_code(request.query, request.options)
        return CodeSearchResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Code search failed: {str(e)}") 