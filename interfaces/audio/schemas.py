from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional
from datetime import datetime

class AudioProcessingConfig(BaseModel):
    normalize: bool = True
    remove_noise: bool = True
    language: Optional[str] = None

class TranscriptionResponse(BaseModel):
    text: str
    segments: List[Dict]
    language: str
    duration: float
    word_count: int
    confidence: float

class AudioFeatures(BaseModel):
    mfcc: List[float]
    chroma: List[float]
    spectral_centroid: float
    spectral_rolloff: float
    zero_crossing_rate: float
    duration: float

class RecordingConfig(BaseModel):
    max_duration: int = Field(300, gt=0, le=3600)  # 5 minutes default, max 1 hour
    output_format: str = Field("wav", pattern="^(wav|mp3|ogg)$")
    sample_rate: Optional[int] = None
    channels: int = Field(1, ge=1, le=2)

class AudioFile(BaseModel):
    filename: str
    size: int
    duration: float
    format: str
    sample_rate: int
    channels: int
    created_at: datetime
    processed: bool
    transcribed: bool
    
    model_config = ConfigDict(from_attributes=True)

class AudioProcessingResponse(BaseModel):
    original_file: str
    processed_file: str
    processing_time: float
    settings_used: Dict
    output_format: str
    size_reduction: float  # percentage 