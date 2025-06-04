# interfaces/memory/models.py

from pydantic import BaseModel
from uuid import UUID
from typing import List, Optional
from datetime import datetime

class MemoryEntryOut(BaseModel):
    entry_id: UUID
    session_id: str
    timestamp: datetime
    text: str
    tags: List[str]
    pinned: bool
    confidence: Optional[float]
