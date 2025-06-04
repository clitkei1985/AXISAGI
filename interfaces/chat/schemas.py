from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Optional, List, Any
from datetime import datetime

class ChatMessage(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    content: str
    role: str = "user"
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    message_type: str = "text"  # text, file, system
    timestamp: Optional[datetime] = None

class ChatResponse(BaseModel):
    message_id: Optional[int] = None
    content: Optional[str] = None
    response: Optional[str] = None  # For frontend compatibility
    status: str = "success"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    user_message: Optional["Message"] = None  # Pydantic message object
    assistant_message: Optional["Message"] = None  # Pydantic message object

class StreamResponse(BaseModel):
    content: str
    is_complete: bool = False
    message_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SessionCreate(BaseModel):
    title: Optional[str] = "New Chat"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    model_config_data: Optional[Dict[str, Any]] = Field(default_factory=dict)

class SessionUpdate(BaseModel):
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    is_archived: Optional[bool] = None

class ChatSession(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    title: Optional[str] = None
    session_type: str
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)
    start_time: datetime
    is_archived: bool = False

class FileUploadResponse(BaseModel):
    filename: str
    path: str
    type: Optional[str] = None
    size: Optional[int] = None
    analysis: Optional[Dict[str, Any]] = None
    transcription: Optional[Dict[str, Any]] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

class ChatAnalytics(BaseModel):
    total_messages: int
    user_messages: int
    assistant_messages: int
    avg_response_length: float
    session_duration: float  # in seconds
    files_uploaded: int
    memory_enhanced_responses: int
    most_common_topics: Optional[List[str]] = None
    sentiment_distribution: Optional[Dict[str, float]] = None

class WebSocketMessage(BaseModel):
    type: str  # message, typing, status, error
    content: Optional[str] = None
    role: Optional[str] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    message_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None

class TypingIndicator(BaseModel):
    user_id: int
    username: str
    is_typing: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class MessageCreate(BaseModel):
    content: str
    role: str = "user"
    metadata: Optional[Dict] = Field(default_factory=dict)

class MessageUpdate(BaseModel):
    content: Optional[str] = None
    metadata: Optional[Dict] = None

class Message(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    session_id: int
    role: str
    content: str
    timestamp: datetime
    extra_metadata: Dict[str, Any] = Field(default_factory=dict) 