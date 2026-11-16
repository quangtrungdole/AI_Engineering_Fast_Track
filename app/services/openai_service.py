"""Service helpers for calling the OpenAI Responses API.

Configuration is loaded from environment variables, preferably from a local
``.env`` file during development. Never commit the real API key.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal, TypedDict

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DEFAULT_MODEL = "gpt-5.6-luna"
SUPPORTED_FILE_EXTENSIONS = {".md", ".txt"}


class Message(TypedDict):
    role: Literal["developer", "system", "user", "assistant"]
    content: str


def _client() -> OpenAI:
    """Create an authenticated OpenAI client from the environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to .env or the process environment."
        )
    return OpenAI(api_key=api_key)


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
