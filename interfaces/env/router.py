from fastapi import APIRouter
from core.env_detect import detect_all

router = APIRouter(prefix="/api/env", tags=["env"])

@router.get("/", response_model=dict)
def env_info():
    return detect_all()
