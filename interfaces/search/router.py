from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from core.auth import get_current_user

router = APIRouter(prefix="/api/search", tags=["search"])


class SearchRequest(BaseModel):
    session_id: str
    query: str


class SearchResponse(BaseModel):
    status: str
    result: str


@router.get("/", response_model=SearchResponse)
def search_root():
    return SearchResponse(status="ok", result="Search endpoint is live.")


@router.post("/web", response_model=SearchResponse)
def web_search(req: SearchRequest, current_user=Depends(get_current_user)):
    if req.session_id != current_user.session_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return SearchResponse(status="ok", result=f"(echoed query) {req.query}")
