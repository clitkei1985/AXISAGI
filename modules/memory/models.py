# modules/memory/models.py

from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime

class MemoryEntry(BaseModel):
    entry_id: UUID = Field(default_factory=uuid4)
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    text: str
    tags: List[str] = []
    pinned: bool = False
    confidence: Optional[float] = None

class AddMemoryRequest(BaseModel):
    session_id: str
    text: str
    tags: Optional[List[str]] = []
    pinned: Optional[bool] = False

class AddMemoryResponse(BaseModel):
    status: str
    entry_id: UUID

class SearchMemoryRequest(BaseModel):
    session_id: str
    query: str
    top_k: Optional[int] = 5

class SearchMemoryResponse(BaseModel):
    status: str
    results: List[MemoryEntry]

class GetAllMemoryResponse(BaseModel):
    status: str
    entries: List[MemoryEntry]

class DeleteMemoryRequest(BaseModel):
    session_id: str
    entry_id: UUID

class DeleteMemoryResponse(BaseModel):
    status: str
    deleted: bool

class UpdateMemoryRequest(BaseModel):
    session_id: str
    entry_id: UUID
    text: Optional[str] = None
    tags: Optional[List[str]] = None
    pinned: Optional[bool] = None

class UpdateMemoryResponse(BaseModel):
    status: str
    updated: bool
