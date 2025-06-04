from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db, User
from core.security import get_current_active_user
from modules.code_analysis.analyzer import get_code_analyzer
from .schemas import CodeReviewRequest, CodeReviewResult

review_router = APIRouter()

@review_router.post("/review", response_model=CodeReviewResult)
async def review_code(
    request: CodeReviewRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Perform automated code review with detailed feedback. (Features: 41, 103, 110, 114, 116, 117, 118, 119, 132, 133, 136, 204)"""
    analyzer = get_code_analyzer()
    try:
        analysis = await analyzer.analyze_file(request.filename, request.content)
        comments = []
        overall_score = 100.0
        for issue in analysis.issues:
            severity_impact = {
                'critical': 20,
                'high': 15,
                'medium': 10,
                'low': 5
            }
            overall_score -= severity_impact.get(issue.severity, 5)
            comments.append({
                'line': issue.line,
                'type': 'issue',
                'message': issue.message,
                'severity': issue.severity,
                'category': issue.type
            })
        for sec_issue in analysis.security_issues:
            overall_score -= 25
            comments.append({
                'line': sec_issue.line,
                'type': 'issue',
                'message': f"Security: {sec_issue.description}",
                'severity': sec_issue.severity,
                'category': 'security'
            })
        overall_score = max(0, overall_score)
        return CodeReviewResult(
            filename=request.filename,
            comments=comments,
            overall_score=overall_score,
            summary="Automated review complete.",
            recommendations=["Refactor code for clarity.", "Address security issues."]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Code review failed: {str(e)}") 