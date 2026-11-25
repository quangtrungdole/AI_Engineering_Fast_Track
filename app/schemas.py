"""Pydantic contracts for the meeting-analysis API and model output."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class MeetingAnalysisRequest(BaseModel):
    meeting_text: str = Field(min_length=1, max_length=50_000)


class ActionItem(BaseModel):
    owner: str | None = None
    action: str = Field(min_length=1)
    due_date: date | None = None


class MeetingAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1)
    decisions: list[str] = Field(default_factory=list)
    actions: list[ActionItem] = Field(default_factory=list)
