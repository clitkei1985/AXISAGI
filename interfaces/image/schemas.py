from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional, Tuple
from datetime import datetime

class ImageOperations(BaseModel):
    resize: Optional[Tuple[int, int]] = None
    rotate: Optional[float] = None
    filters: Optional[List[str]] = None

class ProcessedImage(BaseModel):
    original_filename: str
    processed_filename: str
    operations: Dict
    size: Dict[str, int]
    format: str
    created_at: datetime

class ObjectDetection(BaseModel):
    class_name: str
    confidence: float
    bbox: Dict[str, int]

class DetectionResult(BaseModel):
    filename: str
    detections: List[ObjectDetection]
    inference_time: float
    model_used: str

class ImageFeatures(BaseModel):
    size: Dict[str, int]
    format: str
    mode: str
    histogram: Dict[str, List[float]]
    color_stats: Dict[str, List[float]]
    edge_density: float

class ImageComparison(BaseModel):
    mse: float
    psnr: float
    histogram_similarity: float
    size_difference: Dict[str, int]

class ImageFile(BaseModel):
    filename: str
    size: int
    format: str
    width: int
    height: int
    created_at: datetime
    processed: bool
    has_objects: bool
    
    model_config = ConfigDict(from_attributes=True) 