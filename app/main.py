"""FastAPI application entry point."""

from fastapi import FastAPI

from app.analyze_meeting import router as meeting_router
from app.retrieval_api import router as retrieval_router

app = FastAPI(title="AI Engineering Fast-Track API")
app.include_router(meeting_router)
app.include_router(retrieval_router)
