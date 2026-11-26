## W02: Meeting analysis API

Set `OPENAI_API_KEY` in a local `.env`, then update the requirements:

```bash
.venv/bin/python -m pip install -r requirements.txt
```

Start the **Meeting analysis API**

```bash
uvicorn app.main:app --reload --port 8000
```

Interactive OpenAPI documentation is available at `http://127.0.0.1:8000/docs`.

```bash
curl -X POST http://127.0.0.1:8000/analyze-meeting \
  -H 'content-type: application/json' \
  -d '{"meeting_text":"Meeting Date: 2026-11-23\\nPhu will review the plan by November 25, 2026."}'
```

The response always follows this shape; absent owner or deadline is `null`:

```json
{"summary":"Phu will review the plan.","decisions":[],"actions":[{"owner":"Phu","action":"Review the plan","due_date":"2026-11-25"}]}
```

The service requests OpenAI Structured Outputs from the Pydantic schema, retries transient
timeouts, connection failures, 429s, and 5xx responses up to three attempts (honoring
`Retry-After` when supplied), and returns 502/504/429 rather than malformed output.

With the API running, create and score the public-fixture predictions. The generated
predictions are stored in `assignments/w02/results/predictions.json`:

```bash
.venv/bin/python assignments/w02/predict_meetings.py
.venv/bin/python assignments/w02/evaluate_meetings.py
```

The evaluator uses the local `sentence-transformers/all-MiniLM-L6-v2` embedding model
for summary, decision, and action-text similarity. Its first run downloads the model
from Hugging Face into the local cache (normally `~/.cache/huggingface/hub`); subsequent
runs reuse the cached model and need no network access once the files are present.
The evaluator reports precision, recall, and F1 for decisions and actions. An action
contains an `action`, owner, and due date: the action text is matched by
semantic similarity, while owner and date use exact matching. This deliberately
model-based metric is stricter than semantic review of summaries. The default similarity
threshold is `0.65`, and can be overridden with `--threshold`.

Evaluation metrics, matching rules, thresholds, and CSV report fields are documented in
[`evaluation_metric.md`](evaluation_metric.md). The evaluator writes the detailed report to
`assignments/w02/results/evaluation_report.csv` and accepts `--threshold` to configure the
semantic matching threshold.

### Error-case tests

The five required error cases are covered by `tests/test_meeting_analysis.py`:

| Error | Test | Expected HTTP status |
| --- | --- | ---: |
| Invalid payload | `test_analyze_meeting_rejects_invalid_payload` | `422` |
| Timeout | `test_analyze_meeting_maps_model_failures` and `test_service_timeout_after_retries_is_504` | `504` |
| `429` | `test_analyze_meeting_maps_model_failures` and `test_service_retries_rate_limit_using_retry_after` | `429` |
| Upstream `500` | `test_analyze_meeting_maps_model_failures` and `test_service_upstream_500_after_retries_is_502` | `502` |
| Malformed model response | `test_analyze_meeting_maps_model_failures` and `test_service_rejects_missing_or_invalid_model_output` | `502` |

Run the automated tests with:

```bash
.venv/bin/python -m pytest tests/test_meeting_analysis.py
```
