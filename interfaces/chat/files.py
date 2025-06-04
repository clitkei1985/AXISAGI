from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db, Session as DBSession, User
from core.security import get_current_active_user
from modules.audio_voice.processor import get_audio_processor
from modules.image_module.processor import get_image_processor
from .schemas import FileUploadResponse
from pathlib import Path
from datetime import datetime

files_router = APIRouter()

@files_router.post("/sessions/{session_id}/upload", response_model=FileUploadResponse)
async def upload_file(
    session_id: int,
    file: UploadFile = File(...),
    process_file: bool = True,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload and optionally process a file in a chat session. (Features: 13, 41, 42, 52, 99, 100, 101, 102, 104, 105, 106, 107, 111, 112, 121, 127, 143, 145, 146, 149, 151, 153, 154)"""
    session = db.query(DBSession).filter(
        DBSession.id == session_id,
        DBSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    uploads_dir = Path("uploads/datasets")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    file_path = uploads_dir / f"{session_id}_{datetime.utcnow().timestamp()}_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    analysis_result = None
    if process_file:
        if file.content_type.startswith("image/"):
            image_processor = get_image_processor()
            analysis_result = await image_processor.analyze_image(str(file_path))
        elif file.content_type.startswith("audio/"):
            audio_processor = get_audio_processor()
            analysis_result = await audio_processor.analyze_audio(str(file_path))
        # Add more file type handlers as needed
    return FileUploadResponse(
        filename=file.filename,
        file_url=str(file_path),
        analysis=analysis_result
    ) 