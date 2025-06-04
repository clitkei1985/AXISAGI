from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from core.auth import get_current_user

router = APIRouter(prefix="/api/user", tags=["user"])


class UserRequest(BaseModel):
    session_id: str
    action: str


class UserResponse(BaseModel):
    status: str
    detail: str


@router.get("/", response_model=UserResponse)
def user_root():
    return UserResponse(status="ok", detail="User endpoint is live.")


@router.post("/info", response_model=UserResponse)
def user_info(req: UserRequest, current_user=Depends(get_current_user)):
    if req.session_id != current_user.session_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    # For now, just echo back
    return UserResponse(status="ok", detail=f"(echoed action) {req.action}")
