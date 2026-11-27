"""Evaluate Week 2 meeting predictions and write a per-case CSV report."""

from __future__ import annotations

import argparse
import csv
from functools import lru_cache
import json
import math
from pathlib import Path
from typing import Any

from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parents[2]
GOLD_PATH = ROOT / "data/evaluation/week2_meeting_notes_expected_20_cases.json"
PREDICTIONS_PATH = Path(__file__).with_name("results") / "predictions.json"
REPORT_PATH = Path(__file__).with_name("results") / "evaluation_report.csv"
DEFAULT_THRESHOLD = 0.65
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def normalize(value: str | None) -> str | None:
    return " ".join(value.lower().split()) if value else None


@lru_cache(maxsize=1)
def _embedding_model() -> SentenceTransformer:
    """Load the pretrained sentence model once per evaluator process."""
    return SentenceTransformer(MODEL_NAME)


@lru_cache(maxsize=4096)
def embedding(text: str | None) -> tuple[float, ...]:
    """Encode text with the locally cached pretrained sentence model."""
    normalized = normalize(text) or ""
    if not normalized:
        return ()
    vector = _embedding_model().encode(normalized, normalize_embeddings=False)
    return tuple(float(value) for value in vector)


def cosine_similarity(left: str | None, right: str | None) -> float:
    first, second = embedding(left), embedding(right)
    if not first or not second:
        return 1.0 if first == second else 0.0
    dot = sum(a * b for a, b in zip(first, second))
    denominator = math.sqrt(sum(value * value for value in first)) * math.sqrt(
        sum(value * value for value in second)
    )
    return dot / denominator if denominator else 0.0


def metric(tp: int, fp: int, fn: int) -> dict[str, float | int | str]:
    if tp == 0 and fp == 0 and fn == 0:
        return {"tp": "null", "fp": "null", "fn": "null", "precision": 1.0, "recall": 1.0, "f1": 1.0}
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def metric_count(value: float | int | str) -> int:
    return 0 if value == "null" else int(value)


def valid_result(result: Any) -> bool:
    return (
        isinstance(result, dict)
        and isinstance(result.get("summary"), str)
        and isinstance(result.get("decisions"), list)
        and isinstance(result.get("actions"), list)
        and all(isinstance(item, str) for item in result["decisions"])
        and all(
            isinstance(item, dict)
            and isinstance(item.get("action"), str)
            and (item.get("owner") is None or isinstance(item.get("owner"), str))
            and (item.get("due_date") is None or isinstance(item.get("due_date"), str))
            for item in result["actions"]
        )
    )


def match_decisions(expected: list[str], predicted: list[str], threshold: float) -> dict[str, float | int]:
    remaining = set(range(len(expected)))
    tp = 0
    for value in predicted:
        candidates = [(cosine_similarity(value, expected[index]), index) for index in remaining]
        if candidates and max(candidates)[0] >= threshold:
            _, index = max(candidates)
            remaining.remove(index)
            tp += 1
    return metric(tp, len(predicted) - tp, len(expected) - tp)


def match_actions(expected: list[dict], predicted: list[dict], threshold: float) -> dict[str, float | int]:
    remaining = set(range(len(expected)))
    tp = 0
    for value in predicted:
        candidates = [
            (
                cosine_similarity(value.get("action"), expected[index].get("action")),
                index,
            )
            for index in remaining
            if normalize(value.get("owner")) == normalize(expected[index].get("owner"))
            and value.get("due_date") == expected[index].get("due_date")
        ]
        if candidates and max(candidates)[0] >= threshold:
            _, index = max(candidates)
            remaining.remove(index)
            tp += 1
    return metric(tp, len(predicted) - tp, len(expected) - tp)


def match_action_field(
    expected: list[dict], predicted: list[dict], field: str
) -> int:
    remaining = set(range(len(expected)))
    correct = 0
    for value in predicted:
        candidates = [
            index
            for index in remaining
            if value.get(field) == expected[index].get(field)
        ]
        if candidates:
            remaining.remove(candidates[0])
            correct += 1
    return correct


def evaluate_case(expected: dict, predicted: Any, threshold: float) -> dict[str, Any]:
    schema_valid = valid_result(predicted)
    actual = predicted if schema_valid else {"summary": "", "decisions": [], "actions": []}
    decision = match_decisions(expected.get("decisions", []), actual["decisions"], threshold)
    action = match_actions(expected.get("actions", []), actual["actions"], threshold)
    summary_similarity = cosine_similarity(expected.get("summary"), actual["summary"])
    expected_actions = expected.get("actions", [])
    owner_total = len(expected_actions)
    owner_correct = match_action_field(
        [{"owner": normalize(item.get("owner"))} for item in expected_actions],
        [{"owner": normalize(item.get("owner"))} for item in actual["actions"]],
        "owner",
    )
    date_correct = match_action_field(expected_actions, actual["actions"], "due_date")
    passed = schema_valid and summary_similarity >= threshold and metric_count(decision["fn"]) == 0 and metric_count(decision["fp"]) == 0 and metric_count(action["fn"]) == 0 and metric_count(action["fp"]) == 0
    reasons = []
    if not schema_valid:
        reasons.append("invalid response schema")
    if summary_similarity < threshold:
        reasons.append("summary similarity below threshold")
    if metric_count(decision["fp"]) or metric_count(decision["fn"]):
        reasons.append("decision extraction mismatch")
    if metric_count(action["fp"]) or metric_count(action["fn"]):
        reasons.append("action extraction mismatch")
    return {"summary_similarity": summary_similarity, "summary_correct": summary_similarity >= threshold, "decision": decision, "action": action, "owner_correct": owner_correct, "owner_total": owner_total, "date_correct": date_correct, "date_total": owner_total, "schema_valid": schema_valid, "passed": passed, "failure_reason": "; ".join(reasons)}


def generate_report(results: list[dict[str, Any]], output_path: Path = REPORT_PATH) -> Path:
    """Write one detailed evaluation row per test case to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["id", "summary_similarity", "summary_correct", "decision_tp", "decision_fp", "decision_fn", "decision_precision", "decision_recall", "decision_f1", "action_tp", "action_fp", "action_fn", "action_precision", "action_recall", "action_f1", "owner_accuracy", "due_date_accuracy", "schema_valid", "fully_passed", "failure_reason"]
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for result in results:
            row = {"id": result["id"], "summary_similarity": result["evaluation"]["summary_similarity"], "summary_correct": result["evaluation"]["summary_correct"], "decision_tp": result["evaluation"]["decision"]["tp"], "decision_fp": result["evaluation"]["decision"]["fp"], "decision_fn": result["evaluation"]["decision"]["fn"], "decision_precision": result["evaluation"]["decision"]["precision"], "decision_recall": result["evaluation"]["decision"]["recall"], "decision_f1": result["evaluation"]["decision"]["f1"], "action_tp": result["evaluation"]["action"]["tp"], "action_fp": result["evaluation"]["action"]["fp"], "action_fn": result["evaluation"]["action"]["fn"], "action_precision": result["evaluation"]["action"]["precision"], "action_recall": result["evaluation"]["action"]["recall"], "action_f1": result["evaluation"]["action"]["f1"], "owner_accuracy": result["evaluation"]["owner_correct"] / result["evaluation"]["owner_total"] if result["evaluation"]["owner_total"] else 1.0, "due_date_accuracy": result["evaluation"]["date_correct"] / result["evaluation"]["date_total"] if result["evaluation"]["date_total"] else 1.0, "schema_valid": result["evaluation"]["schema_valid"], "fully_passed": result["evaluation"]["passed"], "failure_reason": result["evaluation"]["failure_reason"]}
            writer.writerow(row)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate meeting extraction quality and generate a CSV report.")
    parser.add_argument("--predictions", type=Path, default=PREDICTIONS_PATH)
    parser.add_argument("--report", type=Path, default=REPORT_PATH)
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    args = parser.parse_args()
    gold = {case["id"]: case["expected"] for case in json.loads(GOLD_PATH.read_text(encoding="utf-8"))}
    predicted = {row["id"]: row["prediction"] for row in json.loads(args.predictions.read_text(encoding="utf-8"))}
    results = [{"id": case_id, "evaluation": evaluate_case(expected, predicted.get(case_id), args.threshold)} for case_id, expected in gold.items()]
    report_path = generate_report(results, args.report)
    total = len(results)
    decisions = [item["evaluation"]["decision"] for item in results]
    actions = [item["evaluation"]["action"] for item in results]
    print(json.dumps({"threshold": args.threshold, "report": str(report_path), "average_summary_similarity": sum(item["evaluation"]["summary_similarity"] for item in results) / total if total else 0.0, "summary_semantic_correctness_rate": sum(item["evaluation"]["summary_correct"] for item in results) / total if total else 0.0, "decision": metric(sum(metric_count(item["tp"]) for item in decisions), sum(metric_count(item["fp"]) for item in decisions), sum(metric_count(item["fn"]) for item in decisions)), "action": metric(sum(metric_count(item["tp"]) for item in actions), sum(metric_count(item["fp"]) for item in actions), sum(metric_count(item["fn"]) for item in actions)), "owner_accuracy": sum(item["evaluation"]["owner_correct"] for item in results) / sum(item["evaluation"]["owner_total"] for item in results) if sum(item["evaluation"]["owner_total"] for item in results) else 1.0, "due_date_accuracy": sum(item["evaluation"]["date_correct"] for item in results) / sum(item["evaluation"]["date_total"] for item in results) if sum(item["evaluation"]["date_total"] for item in results) else 1.0, "schema_validation_rate": sum(item["evaluation"]["schema_valid"] for item in results) / total if total else 0.0, "fully_passing": f"{sum(item['evaluation']['passed'] for item in results)}/{total}"}, indent=2))


if __name__ == "__main__":
    main()
