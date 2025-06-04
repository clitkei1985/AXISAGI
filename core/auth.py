# core/auth.py

from fastapi import Depends, HTTPException
from pydantic import BaseModel

class User(BaseModel):
    session_id: str

def get_current_user():
    # Stub: always return a “default” user for now
    return User(session_id="default-session")
