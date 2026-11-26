# Weekly Submission – W02 / Member dlqtrung

**Feature (F01–F04 or Foundation):** Foundation — meeting-note analysis with structured AI output

**What I studied (2–3 concepts):**

1. **OpenAI API setup and Python SDK:** I studied how to configure an API key
   and make a model request using the Python SDK, then applied it in the
   meeting-analysis service.
   [OpenAI Developer quickstart](https://developers.openai.com/api/docs/quickstart)
2. **Structured Outputs and schema validation:** I used a Pydantic schema with
   OpenAI Structured Outputs so meeting analysis returns validated summary,
   decision, and action fields rather than relying on unconstrained JSON.
   [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
3. **Transient API errors, timeouts, and rate limits:** I studied API error
   handling and the need to bound retries. For rate limits, honor `Retry-After`
   when present; otherwise use bounded exponential backoff. OpenAI SDK retries
   some transient failures automatically, so those attempts must be considered
   when reasoning about total retries.
   [OpenAI error codes](https://developers.openai.com/api/docs/guides/error-codes) ·
   [Troubleshooting API rate limits and 429 errors](https://help.openai.com/en/articles/5955604-troubleshooting-api-rate-limits-and-429-errors)

**What I built (summary + key modules):**

- Implemented a meeting-analysis API that extracts a concise summary, explicit
  decisions, and assigned actions with owners and ISO-8601 due dates.
- `app/services/openai_service.py` calls the OpenAI Responses API using
  Structured Outputs, validates the parsed result, and retries transient
  timeouts, connection failures, `429` responses, and upstream `5xx` responses.
- `app/schemas.py` defines the validated meeting-analysis response schema;
  `app/prompts/meeting_analysis.md` guides evidence-grounded extraction and
  requires `null` for unsupported owners or due dates.
- `assignments/w02/predict_meetings.py` runs predictions against the 20 public
  fixtures. `assignments/w02/evaluate_meetings.py` evaluates them using local
  `sentence-transformers/all-MiniLM-L6-v2` cosine similarity for text and exact
  matching for normalized owners and due dates.
- `assignments/w02/results/evaluation_report.csv` contains per-case metrics;
  [`assignments/w02/evaluation_metric.md`](../assignments/w02/evaluation_metric.md)
  describes the matching rules, score interpretation, threshold, and report
  columns.
- `tests/test_meeting_analysis.py` covers API behavior and failure handling,
  including invalid payload, timeout, `429`, upstream `500`, and malformed
  model-response cases.

**How to run:**

From the repository root, set `OPENAI_API_KEY` in `.env` and install the
requirements:

```bash
.venv/bin/python -m pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The interactive API documentation is at `http://127.0.0.1:8000/docs`. With the
API running, create predictions and evaluate the 20 public fixtures:

```bash
.venv/bin/python assignments/w02/predict_meetings.py
.venv/bin/python assignments/w02/evaluate_meetings.py
```

Run the API tests, including the error-case coverage:

```bash
.venv/bin/python -m pytest tests/test_meeting_analysis.py
```

The evaluator downloads the embedding model on its first run and reuses the
local Hugging Face cache on subsequent runs; no hosted embedding API is used.

**Results:**

Fresh evaluation of all 20 fixtures with the default threshold `0.65`:

| Metric | Result |
| --- | ---: |
| Average summary cosine similarity | 0.7910 |
| Summary semantic correctness | 19/20 (95%) |
| Decision precision / recall / F1 | 1.000 / 1.000 / 1.000 |
| Action precision / recall / F1 | 0.919 / 0.919 / 0.919 (34 TP, 3 FP, 3 FN) |
| Owner accuracy | 100% |
| Due-date accuracy | 100% |
| Schema validation | 100% |
| Fully passing cases | 17/20 |

The error-case tests cover invalid payload (`422`), timeout (`504`), rate limit
(`429`), upstream `500` (`502`), and malformed model response (`502`). The
evaluator command completed successfully and wrote
`assignments/w02/results/evaluation_report.csv`.

**Known failures / trade-offs:**

- Three fixtures do not fully pass: TC05 and TC06 have action extraction
  mismatches; TC13 has summary similarity below the `0.65` threshold.
- The `0.65` cutoff is the midpoint of the documented moderate-similarity band
  (`0.5`–`0.8`), an operational choice rather than a measured average or a
  probability of correctness.
- First-time evaluation requires downloading the pretrained embedding model;
  later runs can use the cached model offline. API prediction still requires
  an OpenAI API key and network access.
- Model outputs can vary by model and API configuration, and the public set of
  20 fixtures may not represent unseen meeting notes.

**Demo link:**
None

**PR link:**
None

**Next action:**
Review the failed cases to identify their causes, then prepare for the Week 3
assignment.
