from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional
from datetime import datetime

class MemoryBase(BaseModel):
    content: str
    metadata: Optional[Dict] = Field(default_factory=dict)
    source: Optional[str] = None
    privacy_level: str = "private"
    tags: List[str] = Field(default_factory=list)
    project_id: Optional[int] = None

class MemoryCreate(MemoryBase):
    pass

class MemoryUpdate(BaseModel):
    content: Optional[str] = None
    metadata: Optional[Dict] = None
    tags: Optional[List[str]] = None
    privacy_level: Optional[str] = None

class MemoryResponse(MemoryBase):
    id: int
    user_id: int
    embedding_vector: str  # Base64 encoded
    timestamp: datetime
    last_accessed: Optional[datetime]
    access_count: int
    is_pinned: bool
    
    model_config = ConfigDict(from_attributes=True)

class BatchMemoryCreate(BaseModel):
    items: List[MemoryCreate]

class MemorySearch(BaseModel):
    query: str
    k: int = 5
    privacy_levels: Optional[List[str]] = None
    project_id: Optional[int] = None
    min_similarity: float = 0.7

class MemoryStats(BaseModel):
    total_memories: int
    total_size: int  # in bytes
    by_privacy_level: Dict[str, int]
    by_source: Dict[str, int]
    by_project: Dict[int, int]
    access_stats: Dict[str, int]  # includes avg, max, min access counts
    last_cleanup: Optional[datetime] 