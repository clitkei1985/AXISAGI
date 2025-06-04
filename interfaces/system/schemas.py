from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

# Domain Switching Schemas
class ModelPerformanceRequest(BaseModel):
    model_name: str
    domain: str
    performance_score: float

# Lineage Tracking Schemas
class LineageStartRequest(BaseModel):
    query: str
    session_id: Optional[int] = None

class LineageSourceRequest(BaseModel):
    source_type: str
    description: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    confidence: float = 1.0

class ReasoningStepRequest(BaseModel):
    step_type: str
    input_sources: List[str]
    output_data: str
    reasoning_text: str
    confidence: float = 1.0
    model_used: Optional[str] = None

class LineageFinalizeRequest(BaseModel):
    final_answer: str

# Persona Management Schemas
class PersonaSwitchRequest(BaseModel):
    persona_name: str

class CreatePersonaRequest(BaseModel):
    persona_data: Dict[str, Any]

# Response Schemas
class SystemHealthResponse(BaseModel):
    live_reloading: bool
    domain_switching: bool
    lineage_tracking: bool
    persona_management: bool
    timestamp: str

class FeatureInfo(BaseModel):
    id: int
    name: str
    description: str
    status: str

class SystemFeaturesResponse(BaseModel):
    features: Dict[str, FeatureInfo] 