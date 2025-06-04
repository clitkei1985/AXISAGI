# interfaces/chat/router.py

from fastapi import APIRouter
from .sessions import sessions_router
from .messages import messages_router
from .files import files_router
from .analytics import analytics_router
from .websocket import websocket_router

router = APIRouter()
router.include_router(sessions_router)
router.include_router(messages_router)
router.include_router(files_router)
router.include_router(analytics_router)
router.include_router(websocket_router)
