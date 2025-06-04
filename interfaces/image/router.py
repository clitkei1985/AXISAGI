from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import time
from datetime import datetime
from pathlib import Path

from core.database import get_db, User
from core.security import get_current_active_user
from modules.image_module.processor import get_image_processor
from .schemas import (
    ImageOperations,
    ProcessedImage,
    ObjectDetection,
    DetectionResult,
    ImageFeatures,
    ImageComparison,
    ImageFile
)

router = APIRouter()

@router.post("/process", response_model=ProcessedImage)
async def process_image(
    file: UploadFile = File(...),
    operations: ImageOperations = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Process image with specified operations."""
    if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
        raise HTTPException(status_code=400, detail="Unsupported file format")
    
    processor = get_image_processor()
    
    try:
        output_path, metadata = await processor.process_image(
            file.file,
            operations.dict(exclude_unset=True) if operations else {}
        )
        
        # Get processed image info
        img = Image.open(output_path)
        
        return ProcessedImage(
            original_filename=file.filename,
            processed_filename=os.path.basename(output_path),
            operations=metadata,
            size={"width": img.size[0], "height": img.size[1]},
            format=img.format.lower(),
            created_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/detect", response_model=DetectionResult)
async def detect_objects(
    file: UploadFile = File(...),
    confidence: float = Form(0.5),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Detect objects in image using YOLO."""
    if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        raise HTTPException(status_code=400, detail="Unsupported file format")
    
    processor = get_image_processor()
    
    try:
        start_time = time.time()
        detections = await processor.detect_objects(file.file, confidence)
        inference_time = time.time() - start_time
        
        return DetectionResult(
            filename=file.filename,
            detections=[
                ObjectDetection(
                    class_name=d["class"],
                    confidence=d["confidence"],
                    bbox=d["bbox"]
                )
                for d in detections
            ],
            inference_time=inference_time,
            model_used=processor.yolo_model.model.name
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/features", response_model=ImageFeatures)
async def extract_features(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Extract image features for analysis."""
    if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
        raise HTTPException(status_code=400, detail="Unsupported file format")
    
    processor = get_image_processor()
    
    try:
        features = await processor.extract_features(file.file)
        return ImageFeatures(**features)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compare", response_model=ImageComparison)
async def compare_images(
    image1: UploadFile = File(...),
    image2: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Compare two images and compute similarity metrics."""
    processor = get_image_processor()
    
    try:
        comparison = await processor.compare_images(image1.file, image2.file)
        return ImageComparison(**comparison)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/files", response_model=List[ImageFile])
async def list_images(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all processed images."""
    image_dir = Path("uploads/images")
    if not image_dir.exists():
        return []
    
    files = []
    for file_path in image_dir.glob("*.*"):
        if file_path.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
            try:
                img = Image.open(file_path)
                stats = os.stat(file_path)
                
                files.append(ImageFile(
                    filename=file_path.name,
                    size=stats.st_size,
                    format=img.format.lower(),
                    width=img.size[0],
                    height=img.size[1],
                    created_at=datetime.fromtimestamp(stats.st_ctime),
                    processed=file_path.stem.startswith("processed_"),
                    has_objects=False  # Could check for detection results if stored
                ))
            except Exception as e:
                logger.error(f"Error reading image {file_path}: {e}")
    
    return sorted(files, key=lambda x: x.created_at, reverse=True)

@router.get("/download/{filename}")
async def download_image(
    filename: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Download processed image."""
    file_path = Path("uploads/images") / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(
        str(file_path),
        media_type=f"image/{file_path.suffix.lower()[1:]}"
    )
