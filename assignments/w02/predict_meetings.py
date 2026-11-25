"""Call the Week 2 API for every public evaluation input."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = ROOT / "data/evaluation/week2_meeting_notes_expected_20_cases.json"
OUTPUT_PATH = Path(__file__).with_name("results") / "predictions.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()
    cases = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    predictions = []
    with httpx.Client(base_url=args.base_url, timeout=60) as client:
        for case in cases:
            print(f"Meeting text:\n{case["input"]}\n")
            response = client.post("/analyze-meeting", json={"meeting_text": case["input"]})
            response.raise_for_status()
            print(f"Prediction:\n{response.json()}\n")
            predictions.append({"id": case["id"], "prediction": response.json()})
            print(f"-----------------------------------------------------------\n")

    args.output.write_text(json.dumps(predictions, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
