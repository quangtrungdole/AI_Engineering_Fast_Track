from types import SimpleNamespace
from unittest.mock import Mock, patch

import httpx
import pytest
from fastapi.testclient import TestClient
from openai import APITimeoutError, InternalServerError, RateLimitError

from app.main import app
from app.schemas import MeetingAnalysis
from app.services import openai_service
from app.services.openai_service import ModelResponseError, ModelServiceError

client = TestClient(app)


def test_analyze_meeting_returns_structured_response():
    analysis = MeetingAnalysis(summary="Brief summary", decisions=["Proceed"], actions=[])
    with patch("app.analyze_meeting.analyze_meeting", return_value=analysis):
        response = client.post("/analyze-meeting", json={"meeting_text": "Meeting notes"})

    assert response.status_code == 200
    assert response.json() == {"summary": "Brief summary", "decisions": ["Proceed"], "actions": []}


def test_analyze_meeting_rejects_invalid_payload():
    response = client.post("/analyze-meeting", json={"meeting_text": ""})
    assert response.status_code == 422


@pytest.mark.parametrize(
    ("error", "status"),
    [
        (ModelServiceError(504, "Model request timed out"), 504),
        (ModelServiceError(429, "Model rate limit exceeded; retry later"), 429),
        (ModelServiceError(502, "Model service is unavailable"), 502),
        (ModelResponseError("bad structured output"), 502),
    ],
)
def test_analyze_meeting_maps_model_failures(error: Exception, status: int):
    with patch("app.analyze_meeting.analyze_meeting", side_effect=error):
        response = client.post("/analyze-meeting", json={"meeting_text": "Meeting notes"})
    assert response.status_code == status


def test_service_uses_pydantic_structured_output():
    parsed = MeetingAnalysis(summary="Summary", decisions=[], actions=[])
    upstream = Mock()
    upstream.responses.parse.return_value = SimpleNamespace(output_parsed=parsed)
    with patch.object(openai_service, "_client", return_value=upstream), patch.object(
        openai_service, "_meeting_prompt", return_value="instructions"
    ):
        assert openai_service.analyze_meeting("Notes") == parsed

    assert upstream.responses.parse.call_args.kwargs["text_format"] is MeetingAnalysis
    assert upstream.responses.parse.call_args.kwargs["reasoning"] == {"effort": "none"}


def test_service_passes_custom_reasoning_effort():
    parsed = MeetingAnalysis(summary="Summary", decisions=[], actions=[])
    upstream = Mock()
    upstream.responses.parse.return_value = SimpleNamespace(output_parsed=parsed)
    reasoning = "low"
    with patch.object(openai_service, "_client", return_value=upstream), patch.object(
        openai_service, "_meeting_prompt", return_value="instructions"
    ):
        assert openai_service.analyze_meeting("Notes", reasoning=reasoning) == parsed

    assert upstream.responses.parse.call_args.kwargs["reasoning"] == {"effort": reasoning}


def test_service_retries_rate_limit_using_retry_after():
    request = httpx.Request("POST", "https://api.openai.com/v1/responses")
    response = httpx.Response(429, headers={"retry-after": "0.25"}, request=request)
    rate_limited = RateLimitError("rate limited", response=response, body=None)
    parsed = MeetingAnalysis(summary="Summary", decisions=[], actions=[])
    upstream = Mock()
    upstream.responses.parse.side_effect = [rate_limited, SimpleNamespace(output_parsed=parsed)]
    sleeps: list[float] = []
    with patch.object(openai_service, "_client", return_value=upstream), patch.object(
        openai_service, "_meeting_prompt", return_value="instructions"
    ):
        assert openai_service.analyze_meeting("Notes", sleep=sleeps.append) == parsed
    assert sleeps == [0.25]


def test_service_timeout_after_retries_is_504():
    timeout = APITimeoutError(request=httpx.Request("POST", "https://api.openai.com/v1/responses"))
    upstream = Mock()
    upstream.responses.parse.side_effect = timeout
    with patch.object(openai_service, "_client", return_value=upstream), patch.object(
        openai_service, "_meeting_prompt", return_value="instructions"), pytest.raises(
        ModelServiceError, match="timed out"
    ) as raised:
        openai_service.analyze_meeting("Notes", sleep=lambda _: None)
    assert raised.value.status_code == 504


def test_service_upstream_500_after_retries_is_502():
    request = httpx.Request("POST", "https://api.openai.com/v1/responses")
    error = InternalServerError("error", response=httpx.Response(500, request=request), body=None)
    upstream = Mock()
    upstream.responses.parse.side_effect = error
    with patch.object(openai_service, "_client", return_value=upstream), patch.object(
        openai_service, "_meeting_prompt", return_value="instructions"
    ), pytest.raises(ModelServiceError, match="unavailable") as raised:
        openai_service.analyze_meeting("Notes", sleep=lambda _: None)
    assert raised.value.status_code == 502


def test_service_rejects_missing_or_invalid_model_output():
    upstream = Mock()
    upstream.responses.parse.return_value = SimpleNamespace(output_parsed=None)
    with patch.object(openai_service, "_client", return_value=upstream), patch.object(
        openai_service, "_meeting_prompt", return_value="instructions"), pytest.raises(
        ModelResponseError
    ):
        openai_service.analyze_meeting("Notes")
