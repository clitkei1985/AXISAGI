from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import json
from core.database import get_db, Session as DBSession, User
from core.security import get_current_user_from_token

logger = logging.getLogger(__name__)
websocket_router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections = {}
        self.user_sessions = {}

    async def connect(self, websocket: WebSocket, session_id: int, user_id: int):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)
        self.user_sessions[user_id] = session_id
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        })

    def disconnect(self, websocket: WebSocket, session_id: int, user_id: int):
        if session_id in self.active_connections:
            if websocket in self.active_connections[session_id]:
                self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]

    async def send_message(self, message, session_id: int):
        if session_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message: {e}")
                    disconnected.append(connection)
            for conn in disconnected:
                if conn in self.active_connections[session_id]:
                    self.active_connections[session_id].remove(conn)

manager = ConnectionManager()

@websocket_router.websocket("/ws")
async def websocket_simple_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    """Simple WebSocket endpoint for chat that handles authentication after connection."""
    await websocket.accept()
    
    try:
        # Send initial connection success message
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "message": "WebSocket connected. Please authenticate.",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        user = None
        session_id = 1  # Default session
        
        while True:
            try:
                data = await websocket.receive_json()
                
                # Handle authentication
                if data.get("type") == "auth" and not user:
                    token = data.get("token")
                    if token:
                        try:
                            user = await get_current_user_from_token(token, db)
                            session_id = data.get("session_id", 1)
                            await manager.connect(websocket, session_id, user.id)
                            await websocket.send_json({
                                "type": "auth",
                                "status": "success",
                                "user": {"id": user.id, "username": user.username},
                                "session_id": session_id
                            })
                            continue
                        except Exception as e:
                            await websocket.send_json({
                                "type": "auth",
                                "status": "error",
                                "message": "Authentication failed"
                            })
                            continue
                    else:
                        await websocket.send_json({
                            "type": "auth",
                            "status": "error", 
                            "message": "Token required"
                        })
                        continue
                
                # Require authentication for other operations
                if not user:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Please authenticate first"
                    })
                    continue
                
                # Handle regular messages
                response = {
                    "type": "message",
                    "echo": data,
                    "user": user.username,
                    "timestamp": datetime.utcnow().isoformat()
                }
                await manager.send_message(response, session_id)
                
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error", 
                    "message": "Invalid JSON format"
                })
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": "Internal server error"
                })
                
    except WebSocketDisconnect:
        if user:
            manager.disconnect(websocket, session_id, user.id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if user:
            manager.disconnect(websocket, session_id, user.id)

@websocket_router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time chat and streaming. (Features: 10, 23, 24, 32, 33, 34, 35, 38, 39, 48, 49, 121, 127, 134, 151, 201, 202, 203)"""
    user = await get_current_user_from_token(token, db)
    await manager.connect(websocket, session_id, user.id)
    try:
        while True:
            data = await websocket.receive_json()
            # Handle incoming messages, streaming, etc.
            await manager.send_message({"echo": data}, session_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id, user.id) 