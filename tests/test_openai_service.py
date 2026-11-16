from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from app.services import openai_service


def fake_client(output_text: str = "generated answer") -> Mock:
    client = Mock()
    client.responses.create.return_value = SimpleNamespace(output_text=output_text)
    return client


def test_generate_from_messages_uses_environment_model_without_temperature():
    client = fake_client()
    with patch.dict(
        "os.environ",
        {"OPENAI_API_KEY": "test-key", "OPENAI_MODEL": "test-model"},
        clear=False,
    ), patch.object(openai_service, "_client", return_value=client):
        result = openai_service.generate_from_messages(
            [{"role": "user", "content": "Hello"}]
        )

    assert result == "generated answer"
    client.responses.create.assert_called_once_with(
        model="test-model",
        input=[{"role": "user", "content": "Hello"}],
    )


def test_generate_from_messages_accepts_model_override():
    client = fake_client()
    with patch.object(openai_service, "_client", return_value=client):
        openai_service.generate_from_messages(
            [{"role": "developer", "content": "Be brief."}],
            model="override-model",
        )

    client.responses.create.assert_called_once_with(
        model="override-model",
        input=[{"role": "developer", "content": "Be brief."}],
    )


def test_generate_from_text_sends_user_message():
    with patch.object(
        openai_service, "generate_from_messages", return_value="answer"
    ) as generate:
        result = openai_service.generate_from_text("Summarize this")

    assert result == "answer"
    generate.assert_called_once_with(
        [{"role": "user", "content": "Summarize this"}],
        model=None,
    )


def test_generate_from_file_reads_markdown(tmp_path: Path):
    source = tmp_path / "input.md"
    source.write_text("Document content", encoding="utf-8")

    with patch.object(
        openai_service, "generate_from_text", return_value="answer"
    ) as generate:
        result = openai_service.generate_from_file(source)

    assert result == "answer"
    generate.assert_called_once_with("Document content", model=None)


def test_generate_from_file_rejects_unsupported_extension(tmp_path: Path):
    source = tmp_path / "input.pdf"
    source.write_text("not supported", encoding="utf-8")

    with pytest.raises(ValueError, match=".md or .txt"):
        openai_service.generate_from_file(source)


def test_generate_requires_api_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY is not set"):
        openai_service._client()
