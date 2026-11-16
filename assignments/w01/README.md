# W01 issue classification

This exercise sends all 20 issue texts from
`data/evaluation/issue_classification_gold.json` in one OpenAI request. The
gold `category` and `priority` fields are intentionally excluded from the
prompt.

## Setup

From the repository root:

```bash
cp .env.example .env
# Set OPENAI_API_KEY in .env
```

The default model is read from `OPENAI_MODEL` and falls back to
`gpt-5.6-luna`.

## Run

Run each prompt version and save its predictions separately:

```bash
python assignments/w01/classify_issues.py \
  --prompt assignments/w01/prompts/prompt_v1.md \
  --output assignments/w01/results/issue_predictions_v1.csv

python assignments/w01/classify_issues.py \
  --prompt assignments/w01/prompts/prompt_v2.md \
  --output assignments/w01/results/issue_predictions_v2.csv

python assignments/w01/classify_issues.py \
  --prompt assignments/w01/prompts/prompt_v3.md \
  --output assignments/w01/results/issue_predictions_v3.csv
```

Evaluate each output independently:

```bash
python scripts/evaluate_issue_classifier.py \
  assignments/w01/results/issue_predictions_v1.csv

python scripts/evaluate_issue_classifier.py \
  assignments/w01/results/issue_predictions_v2.csv

python scripts/evaluate_issue_classifier.py \
  assignments/w01/results/issue_predictions_v3.csv
```

The default command below writes `results/issue_predictions.csv` when no
custom output path is provided:

```bash
python assignments/w01/classify_issues.py
```

Each output file uses the required header:

```text
issue_id,predicted_category,predicted_priority
```

Then score the result:

```bash
python scripts/evaluate_issue_classifier.py \
  assignments/w01/results/issue_predictions.csv
```

Use a different prompt, model, or output file with the optional flags:

```bash
python assignments/w01/classify_issues.py \
  --prompt assignments/w01/prompts/prompt_v1.md \
  --model gpt-5.6-luna \
  --output assignments/w01/results/issue_predictions.csv
```

## Prompt versions

- `prompts/prompt_v1.md` is the initial version for review.
- `prompts/prompt_v2.md` strengthens the P1 decision rules and critical-risk checks.
- `prompts/prompt_v3.md` adds calibration for operational reporting, cadence,
  incident governance, and P2/P3 boundary cases.

The response is validated with Pydantic before CSV creation. The model's
`next_action` is validated but is not included in the evaluator CSV because the
provided scoring script expects only `issue_id`, `predicted_category`, and
`predicted_priority`.
