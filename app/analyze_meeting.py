"""HTTP endpoint for structured meeting-note extraction."""

from fastapi import APIRouter, HTTPException

from app.schemas import MeetingAnalysis, MeetingAnalysisRequest
from app.services.openai_service import (
    ModelResponseError,
    ModelServiceError,
    analyze_meeting,
)

router = APIRouter(tags=["meetings"])


@router.post("/analyze-meeting", response_model=MeetingAnalysis)
def analyze_meeting_endpoint(payload: MeetingAnalysisRequest) -> MeetingAnalysis:
    try:
        return analyze_meeting(payload.meeting_text)
    except ModelResponseError as exc:
        raise HTTPException(status_code=502, detail="Model returned an invalid response") from exc
    except ModelServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.public_message) from exc
