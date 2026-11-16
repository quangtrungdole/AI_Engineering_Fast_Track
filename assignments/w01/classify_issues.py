"""Batch-classify the W01 issue fixtures with one OpenAI request."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

W01_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = W01_ROOT.parents[1]
DEFAULT_GOLD_PATH = PROJECT_ROOT / "data/evaluation/issue_classification_gold.json"
DEFAULT_PROMPT_PATH = W01_ROOT / "prompts/prompt_v1.md"
DEFAULT_RESULTS_PATH = W01_ROOT / "results/issue_predictions.csv"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.openai_service import generate_from_text


class IssueInput(BaseModel):
    """The only gold-fixture fields allowed into the model prompt."""

    issue_id: str
    text: str


class IssueClassification(BaseModel):
    """One model classification validated against the W01 schema."""

    issue_id: str
    category: Literal["Bug", "Feature", "Question", "Risk"]
    priority: Literal["P1", "P2", "P3"]
    next_action: str = Field(min_length=1)


def load_issue_inputs(gold_path: str | Path = DEFAULT_GOLD_PATH) -> list[IssueInput]:
    """Extract only ``issue_id`` and ``text`` from the gold JSON file."""
    records = json.loads(Path(gold_path).read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError("gold file must contain a JSON array")

    issues = [IssueInput.model_validate(record) for record in records]
    if len({issue.issue_id for issue in issues}) != len(issues):
        raise ValueError("gold file contains duplicate issue_id values")
    return issues


def build_batch_prompt(
    prompt_path: str | Path = DEFAULT_PROMPT_PATH,
    issues: list[IssueInput] | None = None,
) -> str:
    """Combine the reviewed prompt with the batch of issue text inputs."""
    if issues is None:
        issues = load_issue_inputs()
    issue_payload = json.dumps(
        [issue.model_dump() for issue in issues],
        ensure_ascii=False,
        indent=2,
    )
    return f"{Path(prompt_path).read_text(encoding='utf-8').strip()}\n\nIssues:\n{issue_payload}"


def _parse_json_response(response_text: str) -> list[dict[str, object]]:
    """Parse a JSON array, accepting an optional markdown code fence."""
    cleaned = response_text.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL)
    if fenced:
        cleaned = fenced.group(1)
    parsed = json.loads(cleaned)
    if not isinstance(parsed, list):
        raise ValueError("model response must be a JSON array")
    return parsed


def parse_classifications(
    response_text: str,
    expected_issue_ids: set[str],
) -> list[IssueClassification]:
    """Validate model JSON and ensure every requested issue appears exactly once."""
    classifications = [
        IssueClassification.model_validate(item)
        for item in _parse_json_response(response_text)
    ]
    actual_issue_ids = [item.issue_id for item in classifications]
    if len(set(actual_issue_ids)) != len(actual_issue_ids):
        raise ValueError("model response contains duplicate issue_id values")
    if set(actual_issue_ids) != expected_issue_ids:
        raise ValueError("model response issue_id values do not match the input batch")
    return classifications


def classify_issues(
    gold_path: str | Path = DEFAULT_GOLD_PATH,
    prompt_path: str | Path = DEFAULT_PROMPT_PATH,
    *,
    model: str | None = None,
) -> list[IssueClassification]:
    """Send the complete issue batch in one request and validate the response."""
    issues = load_issue_inputs(gold_path)
    response_text = generate_from_text(build_batch_prompt(prompt_path, issues), model=model)
    print("\nOpenAI response:\n")
    print(response_text)
    return parse_classifications(response_text, {issue.issue_id for issue in issues})


def write_predictions_csv(
    classifications: list[IssueClassification],
    output_path: str | Path = DEFAULT_RESULTS_PATH,
) -> Path:
    """Write the evaluator-compatible CSV, excluding the narrative next action."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(
            output,
            fieldnames=["issue_id", "predicted_category", "predicted_priority"],
        )
        writer.writeheader()
        writer.writerows(
            {
                "issue_id": item.issue_id,
                "predicted_category": item.category,
                "predicted_priority": item.priority,
            }
            for item in classifications
        )
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", type=Path, default=DEFAULT_GOLD_PATH)
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_RESULTS_PATH)
    parser.add_argument("--model", default=None)
    args = parser.parse_args()

    classifications = classify_issues(args.gold, args.prompt, model=args.model)
    output_path = write_predictions_csv(classifications, args.output)
    print(f"Wrote {len(classifications)} predictions to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
