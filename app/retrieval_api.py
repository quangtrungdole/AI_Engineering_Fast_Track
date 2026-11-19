"""Project-scoped document search routes mounted by the main FastAPI app."""
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.services.vector_store import SearchResult, search

router = APIRouter()

class SearchRequest(BaseModel):
    """Input for the Week 3 project-scoped document search endpoint."""
    query: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)

@router.post("/search", response_model=list[SearchResult])
def search_documents(
    request: SearchRequest, x_allowed_project: str | None = Header(default=None)
) -> list[SearchResult]:
    """Search chunks only after confirming access to the requested project."""
    if x_allowed_project != request.project_id.upper():
        raise HTTPException(status_code=403, detail="Training access denied")
    return search(request.query, request.project_id, top_k=request.top_k)