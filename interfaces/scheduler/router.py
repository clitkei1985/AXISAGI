from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from core.auth import get_current_user

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])


class ScheduleRequest(BaseModel):
    session_id: str
    message: str


class ScheduleResponse(BaseModel):
    status: str
    job_id: str


@router.get("/", response_model=ScheduleResponse)
def scheduler_root():
    return ScheduleResponse(status="ok", job_id="none")


@router.post("/remind", response_model=ScheduleResponse)
def schedule_reminder(req: ScheduleRequest, current_user=Depends(get_current_user)):
    if req.session_id != current_user.session_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return ScheduleResponse(status="ok", job_id=f"echo_{req.message}")
