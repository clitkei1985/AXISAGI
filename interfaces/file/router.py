from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from core.auth import get_current_user

router = APIRouter(prefix="/api/file", tags=["file"])


class FileRequest(BaseModel):
    session_id: str
    filename: str


class FileResponse(BaseModel):
    status: str
    detail: str


@router.get("/", response_model=FileResponse)
def file_root():
    return FileResponse(status="ok", detail="File endpoint is live.")


@router.post("/upload", response_model=FileResponse)
def upload_file(req: FileRequest, current_user=Depends(get_current_user)):
    if req.session_id != current_user.session_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    # For now, just echo back
    return FileResponse(status="ok", detail=f"(echoed filename) {req.filename}")
