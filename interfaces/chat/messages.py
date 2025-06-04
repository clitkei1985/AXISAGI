from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from core.database import get_db, Session as DBSession, Message, User
from core.security import get_current_active_user
from modules.llm_engine.engine import get_llm_engine
from .schemas import ChatMessage, ChatResponse

messages_router = APIRouter()

@messages_router.get("/sessions/{session_id}/messages", response_model=List[ChatMessage])
async def list_messages(
    session_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all messages in a chat session. (Features: 6, 10, 23, 24, 38, 39, 48, 49, 121, 127, 134)"""
    session = db.query(DBSession).filter(
        DBSession.id == session_id,
        DBSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return db.query(Message).filter(
        Message.session_id == session_id
    ).order_by(Message.timestamp.desc()).offset(skip).limit(limit).all()

@messages_router.post("/sessions/{session_id}/messages", response_model=ChatResponse)
async def send_message(
    session_id: int,
    message: ChatMessage,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send a message in a chat session and get a response. (Features: 6, 10, 23, 24, 32, 33, 34, 35, 38, 39, 48, 49, 76, 78, 80, 81, 121, 127, 134, 201, 202, 203)"""
    # Validate session
    session = db.query(DBSession).filter(
        DBSession.id == session_id,
        DBSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Save user message
    db_message = Message(
        session_id=session_id,
        content=message.content,
        role="user",
        extra_metadata=message.metadata or {}
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    # Generate response using LLM engine
    try:
        llm_engine = get_llm_engine(db)
        response_text = await llm_engine.generate_response(
            prompt=message.content,
            user=current_user,
            session_id=session_id,
            max_tokens=512,
            temperature=0.7,
            use_memory=True
        )
    except Exception as e:
        response_text = f"Sorry, I'm having trouble generating a response right now. Error: {str(e)}"
    
    # Save assistant message
    assistant_message = Message(
        session_id=session_id,
        content=response_text,
        role="assistant",
        extra_metadata={"session_id": session_id}
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)
    
    return ChatResponse(
        response=response_text,
        message_id=assistant_message.id,
        status="success"
    )

@messages_router.post("/send", response_model=ChatResponse)
async def send_message_simple(
    message: ChatMessage,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send a message and get a response. Creates a session if none exists. (Features: 6, 10, 23, 24, 32, 33, 34, 35, 38, 39, 48, 49, 76, 78, 80, 81, 121, 127, 134, 201, 202, 203)"""
    # Get or create default session
    session = db.query(DBSession).filter(
        DBSession.user_id == current_user.id,
        DBSession.session_type == "chat"
    ).first()
    
    if not session:
        # Create a new session
        session = DBSession(
            user_id=current_user.id,
            session_type="chat",
            extra_metadata={"auto_created": True}
        )
        db.add(session)
        db.commit()
        db.refresh(session)
    
    # Save user message
    db_message = Message(
        session_id=session.id,
        content=message.content,
        role="user",
        extra_metadata=message.metadata or {}
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    # Generate response using LLM engine
    try:
        llm_engine = get_llm_engine(db)
        response_text = await llm_engine.generate_response(
            prompt=message.content,
            user=current_user,
            session_id=session.id,
            max_tokens=512,
            temperature=0.7,
            use_memory=True
        )
    except Exception as e:
        response_text = f"Sorry, I'm having trouble generating a response right now. Error: {str(e)}"
    
    # Save assistant message
    assistant_message = Message(
        session_id=session.id,
        content=response_text,
        role="assistant",
        extra_metadata={"session_id": session.id}
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)
    
    return ChatResponse(
        response=response_text,
        message_id=assistant_message.id,
        status="success"
    ) 