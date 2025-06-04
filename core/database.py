# core/database.py

import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from typing import Dict, List, Optional
import json
from datetime import datetime
from core.config import settings

# Make sure the `db/` directory exists
db_url = settings.memory.sql_db_url
os.makedirs(os.path.dirname(db_url.replace("sqlite:///", "")), exist_ok=True)

# Create the SQLAlchemy engine using the DB_URL from settings
engine = create_engine(db_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    memories = relationship("Memory", back_populates="user")
    sessions = relationship("Session", back_populates="user")
    projects = relationship("Project", back_populates="user")

class Memory(Base):
    __tablename__ = "memories"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    content = Column(Text)
    embedding_vector = Column(String)  # Store as base64 encoded string
    extra_metadata = Column(JSON)
    source = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    last_accessed = Column(DateTime(timezone=True))
    access_count = Column(Integer, default=0)
    is_pinned = Column(Boolean, default=False)
    privacy_level = Column(String)  # private, shared, public
    tags = Column(JSON)  # Store as JSON array
    
    # Relationships
    user = relationship("User", back_populates="memories")
    project = relationship("Project", back_populates="memories")

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    session_type = Column(String)  # chat, code, audio, etc.
    extra_metadata = Column(JSON)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    messages = relationship("Message", back_populates="session")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    role = Column(String)  # user, assistant, system
    content = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    extra_metadata = Column(JSON)
    
    # Relationships
    session = relationship("Session", back_populates="messages")

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    extra_metadata = Column(JSON)
    
    # Relationships
    user = relationship("User", back_populates="projects")
    memories = relationship("Memory", back_populates="project")

class Plugin(Base):
    __tablename__ = "plugins"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    version = Column(String)
    enabled = Column(Boolean, default=True)
    config = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String)
    resource_type = Column(String)
    resource_id = Column(String)
    details = Column(JSON)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)

def init_db():
    """
    Call this at app startup to create tables if they don't already exist.
    """
    create_tables()
