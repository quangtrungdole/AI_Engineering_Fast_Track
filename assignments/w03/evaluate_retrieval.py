"""Compute project-scoped Recall@K against the Week 3 labeled queries.

Usage: python assignments/w03/evaluate_retrieval.py [top_k]
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.services.vector_store import search


# Define the labeled evaluation cases.
GOLD = ROOT / "data/evaluation/retrieval_gold.json"


def main() -> None:
    # Read an optional Recall@K cutoff; default to the assignment's Recall@5.
    top_k = int(sys.argv[1]) if len(sys.argv) == 2 else 5
    if not 1 <= top_k <= 50:
        sys.exit("top_k must be between 1 and 50")

    # Load the 20 labeled queries used to calculate Recall@K.
    cases = json.loads(GOLD.read_text(encoding="utf-8"))
    hits = 0
    for case in cases:
        # Search only inside the labeled case's project scope.
        result_ids = {
            result.doc_id
            for result in search(case["question"], case["project_id"], top_k=top_k)
        }
        # Count a hit when any expected document occurs in the top-K results.
        hit = bool(result_ids.intersection(case["relevant_doc_ids"]))
        hits += hit
        # Show the input and retrieved document IDs for a quick evaluation overview.
        expected_ids = ", ".join(case["relevant_doc_ids"])
        retrieved_ids = ", ".join(sorted(result_ids)) or "(none)"
        outcome = "HIT" if hit else "MISS"
        print(
            f"{case['query_id']} | project={case['project_id']} | {outcome}\n"
            f"  question: {case['question']}\n"
            f"  expected: {expected_ids}\n"
            f"  retrieved: {retrieved_ids}"
        )

    # Report the aggregate Recall@K score.
    print(f"Recall@{top_k}: {hits}/{len(cases)} = {hits / len(cases):.1%}")


if __name__ == "__main__":
    main()
