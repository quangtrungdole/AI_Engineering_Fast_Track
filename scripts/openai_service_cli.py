"""Command-line helpers for testing the OpenAI service functions."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.openai_service import (
    Message,
    generate_from_file,
    generate_from_messages,
    generate_from_text,
)


def _common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--model", help="OpenAI model; defaults to OPENAI_MODEL")


def run_text(args: argparse.Namespace) -> str:
    return generate_from_text(args.text, model=args.model)


def run_file(args: argparse.Namespace) -> str:
    return generate_from_file(args.path, model=args.model)


def run_messages(args: argparse.Namespace) -> str:
    try:
        messages: list[Message] = json.loads(args.messages)
    except json.JSONDecodeError as exc:
        raise ValueError("messages must be valid JSON") from exc
    if not isinstance(messages, list):
        raise ValueError("messages JSON must be an array")
    return generate_from_messages(messages, model=args.model)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    text_parser = subparsers.add_parser("text", help="Generate from text")
    text_parser.add_argument("text")
    _common_arguments(text_parser)
    text_parser.set_defaults(handler=run_text)

    file_parser = subparsers.add_parser("file", help="Generate from .md or .txt")
    file_parser.add_argument("path")
    _common_arguments(file_parser)
    file_parser.set_defaults(handler=run_file)

    messages_parser = subparsers.add_parser(
        "messages", help="Generate from a JSON messages array"
    )
    messages_parser.add_argument(
        "messages",
        help='JSON, for example: [{"role":"user","content":"Hello"}]',
    )
    _common_arguments(messages_parser)
    messages_parser.set_defaults(handler=run_messages)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        print(args.handler(args))
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Error: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
