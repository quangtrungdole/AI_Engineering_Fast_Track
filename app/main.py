"""FastAPI application entry point."""

from fastapi import FastAPI

from app.analyze_meeting import router as meeting_router

app = FastAPI(title="AI Engineering Fast-Track API")
app.include_router(meeting_router)
