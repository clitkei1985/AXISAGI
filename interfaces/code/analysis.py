from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from pathlib import Path
import tempfile
import zipfile
from core.database import get_db, User
from core.security import get_current_active_user
from modules.code_analysis.analyzer import get_code_analyzer
from .schemas import (
    FileAnalysisRequest, AnalysisResult, ProjectAnalysisRequest, ProjectAnalysisResult, DiffAnalysisRequest, DiffAnalysisResult
)

analysis_router = APIRouter()

@analysis_router.post("/analyze/file", response_model=AnalysisResult)
async def analyze_file(
    request: FileAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Analyze a single file for quality, security, and complexity issues. (Features: 41, 103, 110, 114, 116, 117, 118, 119, 132, 133, 136, 204)"""
    analyzer = get_code_analyzer()
    try:
        result = await analyzer.analyze_file(request.filename, request.content)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@analysis_router.post("/analyze/upload", response_model=AnalysisResult)
async def analyze_uploaded_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Analyze an uploaded file. (Features: 41, 103, 110, 114, 116, 117, 118, 119, 132, 133, 136, 204)"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    analyzer = get_code_analyzer()
    try:
        content = await file.read()
        content_str = content.decode('utf-8')
        result = await analyzer.analyze_file(file.filename, content_str)
        return result
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be text-based")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@analysis_router.post("/analyze/project", response_model=ProjectAnalysisResult)
async def analyze_project(
    request: ProjectAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Analyze an entire project directory. (Features: 41, 103, 110, 114, 115, 116, 117, 118, 119, 132, 133, 136, 204)"""
    analyzer = get_code_analyzer()
    try:
        project_path = Path(request.project_path)
        if not project_path.exists():
            raise HTTPException(status_code=404, detail="Project path not found")
        if not str(project_path).startswith('/tmp/') and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Access denied to this path")
        result = await analyzer.analyze_project(str(project_path))
        result['summary']['languages'] = dict(result['summary']['languages'])
        result['summary']['issue_types'] = dict(result['summary']['issue_types'])
        result['summary']['severity_distribution'] = dict(result['summary']['severity_distribution'])
        return ProjectAnalysisResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Project analysis failed: {str(e)}")

@analysis_router.post("/analyze/project/upload", response_model=ProjectAnalysisResult)
async def analyze_project_upload(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Analyze an uploaded project archive (zip file). (Features: 41, 103, 110, 114, 115, 116, 117, 118, 119, 132, 133, 136, 204)"""
    if not file.filename or not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files are supported")
    analyzer = get_code_analyzer()
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = Path(temp_dir) / file.filename
            with open(zip_path, 'wb') as f:
                content = await file.read()
                f.write(content)
            extract_dir = Path(temp_dir) / "extracted"
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            result = await analyzer.analyze_project(str(extract_dir))
            result['summary']['languages'] = dict(result['summary']['languages'])
            result['summary']['issue_types'] = dict(result['summary']['issue_types'])
            result['summary']['severity_distribution'] = dict(result['summary']['severity_distribution'])
            return ProjectAnalysisResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Project analysis failed: {str(e)}")

@analysis_router.post("/diff/analyze", response_model=DiffAnalysisResult)
async def analyze_diff(
    request: DiffAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Analyze code diffs for changes, issues, and improvements. (Features: 53, 112, 114, 116, 117, 118, 204)"""
    analyzer = get_code_analyzer()
    try:
        result = await analyzer.analyze_diff(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diff analysis failed: {str(e)}") 