from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

class SourceType(Enum):
    """Types of data sources"""
    MEMORY = "memory"
    DOCUMENT = "document"
    WEB_SEARCH = "web_search"
    USER_INPUT = "user_input"
    API_CALL = "api_call"
    DATABASE = "database"
    PLUGIN = "plugin"
    MODEL_KNOWLEDGE = "model_knowledge"
    CALCULATION = "calculation"
    REASONING = "reasoning"

@dataclass
class DataSource:
    """Individual data source for lineage tracking"""
    id: str
    source_type: SourceType
    description: str
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime
    confidence: float
    user_id: Optional[int] = None
    session_id: Optional[int] = None

@dataclass
class ReasoningStep:
    """Individual reasoning step in the lineage"""
    id: str
    step_type: str  # "analysis", "synthesis", "deduction", "lookup", etc.
    input_sources: List[str]  # Source IDs used in this step
    output_data: str
    reasoning_text: str
    confidence: float
    timestamp: datetime
    model_used: Optional[str] = None

@dataclass
class LineageTrace:
    """Complete lineage trace for an answer"""
    trace_id: str
    query: str
    final_answer: str
    sources: List[DataSource]
    reasoning_steps: List[ReasoningStep]
    metadata: Dict[str, Any]
    created_at: datetime
    user_id: Optional[int] = None
    session_id: Optional[int] = None 