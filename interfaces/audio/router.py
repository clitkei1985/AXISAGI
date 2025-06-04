from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import time
from datetime import datetime
from pathlib import Path

from core.database import get_db, User
from core.security import get_current_active_user
from modules.audio_voice import get_audio_processor
from .schemas import (
    AudioProcessingConfig,
    TranscriptionResponse,
    AudioFeatures,
    RecordingConfig,
    AudioFile,
    AudioProcessingResponse
)

router = APIRouter()

@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    config: AudioProcessingConfig = AudioProcessingConfig(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Transcribe audio file to text."""
    if not file.filename.lower().endswith(('.wav', '.mp3', '.ogg')):
        raise HTTPException(status_code=400, detail="Unsupported file format")
    
    processor = get_audio_processor()
    
    try:
        start_time = time.time()
        result = await processor.transcribe_file(
            file.file,
            language=config.language
        )
        
        # Calculate additional metrics
        duration = len(result["segments"]) * result["segments"][0]["duration"]
        word_count = len(result["text"].split())
        confidence = sum(s["confidence"] for s in result["segments"]) / len(result["segments"])
        
        return TranscriptionResponse(
            text=result["text"],
            segments=result["segments"],
            language=result["language"],
            duration=duration,
            word_count=word_count,
            confidence=confidence
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/record", response_model=AudioFile)
async def start_recording(
    config: RecordingConfig,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Start recording audio."""
    processor = get_audio_processor()
    
    # Generate unique filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"recording_{timestamp}_{current_user.id}.{config.output_format}"
    output_path = Path("uploads/audio") / filename
    
    try:
        # Start recording in background
        background_tasks.add_task(
            processor.start_recording,
            str(output_path),
            config.max_duration
        )
        
        return AudioFile(
            filename=filename,
            size=0,  # Will be updated when recording completes
            duration=0,  # Will be updated when recording completes
            format=config.output_format,
            sample_rate=config.sample_rate or processor.sample_rate,
            channels=config.channels,
            created_at=datetime.utcnow(),
            processed=False,
            transcribed=False
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process", response_model=AudioProcessingResponse)
async def process_audio(
    file: UploadFile = File(...),
    config: AudioProcessingConfig = AudioProcessingConfig(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Process audio file with noise reduction and normalization."""
    if not file.filename.lower().endswith(('.wav', '.mp3', '.ogg')):
        raise HTTPException(status_code=400, detail="Unsupported file format")
    
    processor = get_audio_processor()
    
    try:
        # Save uploaded file
        input_path = Path("uploads/audio") / f"input_{file.filename}"
        with open(input_path, "wb") as f:
            f.write(file.file.read())
        
        start_time = time.time()
        
        # Process audio
        output_path = await processor.process_audio_file(
            str(input_path),
            normalize=config.normalize,
            remove_noise=config.remove_noise
        )
        
        processing_time = time.time() - start_time
        
        # Calculate size reduction
        original_size = os.path.getsize(input_path)
        processed_size = os.path.getsize(output_path)
        size_reduction = ((original_size - processed_size) / original_size) * 100
        
        return AudioProcessingResponse(
            original_file=file.filename,
            processed_file=os.path.basename(output_path),
            processing_time=processing_time,
            settings_used={
                "normalize": config.normalize,
                "remove_noise": config.remove_noise
            },
            output_format=output_path.split('.')[-1],
            size_reduction=size_reduction
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup input file
        if input_path.exists():
            os.remove(input_path)

@router.get("/features/{filename}", response_model=AudioFeatures)
async def get_audio_features(
    filename: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Extract audio features for analysis."""
    file_path = Path("uploads/audio") / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    processor = get_audio_processor()
    
    try:
        return await processor.extract_audio_features(str(file_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{filename}")
async def download_audio(
    filename: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Download processed audio file."""
    file_path = Path("uploads/audio") / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        str(file_path),
        media_type="audio/wav",
        filename=filename
    )
