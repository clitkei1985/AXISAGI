from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union
from datetime import datetime

class ModelConfig(BaseModel):
    name: str
    type: str  # "openai" or "local"
    max_tokens: int
    temperature: float
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: Optional[List[str]] = None

class GenerationRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    session_id: Optional[int] = None
    max_tokens: int = 2048
    temperature: float = 0.7
    stream: bool = False
    use_memory: bool = True
    force_offline: bool = False

class GenerationResponse(BaseModel):
    response: str
    model_used: str
    tokens_used: int
    offline_mode: bool = False
    memory_enhanced: bool = False
    timestamp: datetime

class StreamChunk(BaseModel):
    content: str
    finish_reason: Optional[str] = None

class SentimentAnalysis(BaseModel):
    positive: float
    negative: float
    neutral: float
    dominant: str
    confidence: float

class ModelStats(BaseModel):
    total_requests: int
    total_tokens: int
    avg_latency_ms: float
    error_rate: float
    last_error: Optional[str]
    last_error_time: Optional[datetime]
    uptime_seconds: int

# Additional schemas for new API endpoints

class ModelLoadRequest(BaseModel):
    model_path: str
    model_name: Optional[str] = None
    device: str = "auto"
    quantization: Optional[str] = "4bit"

class SystemStatusResponse(BaseModel):
    offline_mode: bool
    openai_available: bool
    llama_loaded: bool
    llama_info: Optional[Dict] = None
    local_models: List[str]
    memory_enabled: bool
    prefer_local: bool
    system_stats: Dict
    timestamp: datetime

class ResearchRequest(BaseModel):
    topic: str
    depth: str = "normal"  # "quick", "normal", "deep"
    include_web_search: bool = False
    max_sources: int = 5

class ResearchResponse(BaseModel):
    topic: str
    research_result: str
    sources_consulted: List[str]
    confidence_score: float
    timestamp: datetime

class SentimentRequest(BaseModel):
    text: str
    detailed: bool = False

class SentimentResponse(BaseModel):
    text: str
    sentiment_scores: Dict[str, float]
    dominant_sentiment: str
    confidence: float
    timestamp: datetime 