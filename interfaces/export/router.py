from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from core.auth import get_current_user

router = APIRouter(prefix="/api/export", tags=["export"])


class ExportRequest(BaseModel):
    session_id: str
    what: str


class ExportResponse(BaseModel):
    status: str
    detail: str


@router.get("/", response_model=ExportResponse)
def export_root():
    return ExportResponse(status="ok", detail="Export endpoint is live.")


@router.post("/download", response_model=ExportResponse)
def download(req: ExportRequest, current_user=Depends(get_current_user)):
    if req.session_id != current_user.session_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return ExportResponse(status="ok", detail=f"(echoed export) {req.what}")
