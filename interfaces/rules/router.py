from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from core.auth import get_current_user

router = APIRouter(prefix="/api/rules", tags=["rules"])


class RuleRequest(BaseModel):
    session_id: str


class RuleResponse(BaseModel):
    status: str
    detail: str


@router.get("/", response_model=RuleResponse)
def rules_root():
    return RuleResponse(status="ok", detail="Rules endpoint is live.")
