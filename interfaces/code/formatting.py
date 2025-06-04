from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db, User
from core.security import get_current_active_user
from modules.code_analysis.analyzer import get_code_analyzer
from .schemas import CodeFormattingRequest, FormattingResult

formatting_router = APIRouter()

@formatting_router.post("/format", response_model=FormattingResult)
async def format_code(
    request: CodeFormattingRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Format code according to style guidelines. (Features: 41, 103, 110, 117, 118, 204)"""
    analyzer = get_code_analyzer()
    try:
        result = await analyzer.format_code(request.filename, request.content, request.style)
        return FormattingResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Formatting failed: {str(e)}") 