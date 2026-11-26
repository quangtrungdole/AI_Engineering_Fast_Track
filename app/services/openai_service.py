"""Service helpers for calling the OpenAI Responses API.

Configuration is loaded from environment variables, preferably from a local
``.env`` file during development. Never commit the real API key.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Callable, Literal, TypedDict

from dotenv import load_dotenv
from openai import APIConnectionError, APITimeoutError, APIStatusError, OpenAI, RateLimitError

from app.schemas import MeetingAnalysis

load_dotenv()

DEFAULT_MODEL = "gpt-5.6-luna"
SUPPORTED_FILE_EXTENSIONS = {".md", ".txt"}
MEETING_PROMPT_PATH = Path(__file__).parents[1] / "prompts" / "meeting_analysis.md"
MAX_ATTEMPTS = 3


class Message(TypedDict):
    role: Literal["developer", "system", "user", "assistant"]
    content: str


class ModelServiceError(RuntimeError):
    """An upstream model failure safe to expose as an HTTP error."""

    def __init__(self, status_code: int, public_message: str) -> None:
        super().__init__(public_message)
        self.status_code = status_code
        self.public_message = public_message


class ModelResponseError(RuntimeError):
    """The upstream request succeeded but did not satisfy the output schema."""


def _client() -> OpenAI:
    """Create an authenticated OpenAI client from the environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to .env or the process environment."
        )
    # Retry policy is implemented below so Retry-After can be honored consistently.
    return OpenAI(api_key=api_key, max_retries=0)


def _selected_model(model: str | None) -> str:
    selected_model = model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
    return selected_model


def generate_from_messages(
    messages: list[Message],
    *,
    model: str | None = None,
) -> str:
    """Generate a response from messages containing ``role`` and ``content``."""
    if not messages:
        raise ValueError("messages must contain at least one message")

    selected_model = _selected_model(model)
    response = _client().responses.create(
        model=selected_model,
        input=messages,
    )
    return response.output_text


def generate_from_text(
    text: str,
    *,
    model: str | None = None,
) -> str:
    """Generate a response from one user text prompt."""
    if not text.strip():
        raise ValueError("text must not be empty")
    return generate_from_messages(
        [{"role": "user", "content": text}],
        model=model,
    )


def generate_from_file(
    file_path: str | Path,
    *,
    model: str | None = None,
) -> str:
    """Read a UTF-8 ``.md`` or ``.txt`` file and generate a response."""
    path = Path(file_path)
    if path.suffix.lower() not in SUPPORTED_FILE_EXTENSIONS:
        raise ValueError("file_path must point to a .md or .txt file")
    return generate_from_text(
        path.read_text(encoding="utf-8"),
        model=model,
    )


def _meeting_prompt() -> str:
    return MEETING_PROMPT_PATH.read_text(encoding="utf-8")


def _retry_after_seconds(error: BaseException, attempt: int) -> float:
    response = getattr(error, "response", None)
    headers = getattr(response, "headers", None)
    retry_after = headers.get("retry-after") if headers else None
    try:
        if retry_after is not None:
            return max(0.0, float(retry_after))
    except ValueError:
        pass
    return float(2 ** (attempt - 1))


def analyze_meeting(
    meeting_text: str,
    *,
    model: str | None = None,
    reasoning: str = "none",
    sleep: Callable[[float], None] = time.sleep,
) -> MeetingAnalysis:
    """Extract structured meeting facts, retrying transient upstream failures."""
    if not meeting_text.strip():
        raise ValueError("meeting_text must not be empty")

    client = _client()
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = client.responses.parse(
                model=_selected_model(model),
                input=[
                    {"role": "developer", "content": _meeting_prompt()},
                    {"role": "user", "content": meeting_text},
                ],
                text_format=MeetingAnalysis,
                reasoning={"effort": reasoning},
            )
            parsed = response.output_parsed
            if not isinstance(parsed, MeetingAnalysis):
                raise ModelResponseError("Structured output was missing or invalid")
            return parsed
        except (APITimeoutError, APIConnectionError, RateLimitError) as exc:
            if attempt == MAX_ATTEMPTS:
                if isinstance(exc, RateLimitError):
                    raise ModelServiceError(429, "Model rate limit exceeded; retry later") from exc
                raise ModelServiceError(504, "Model request timed out") from exc
            sleep(_retry_after_seconds(exc, attempt))
        except APIStatusError as exc:
            status = getattr(exc, "status_code", 502)
            if status >= 500 and attempt < MAX_ATTEMPTS:
                sleep(_retry_after_seconds(exc, attempt))
                continue
            if status >= 500:
                raise ModelServiceError(502, "Model service is unavailable") from exc
            raise ModelServiceError(502, "Model request failed") from exc
