# Evaluation Metrics

`evaluate_meetings.py` evaluates every public fixture independently and writes
`results/evaluation_report.csv`. The evaluator uses a configurable similarity
threshold (default `0.65`, via `--threshold`).

## Similarity

Text is normalized by lower-casing and collapsing whitespace, then encoded by
the pretrained `sentence-transformers/all-MiniLM-L6-v2` model. The evaluator
computes cosine similarity between the resulting dense vectors:

`dot(A, B) / (norm(A) * norm(B))`

The model is loaded lazily and cached once per evaluator process; encoded text
vectors are also cached for repeated comparisons. The first run downloads model
files from Hugging Face and stores them in the local Hugging Face cache (normally
`~/.cache/huggingface/hub`). Subsequent runs use the cached files and can run
offline as long as the model is already present. Empty texts match only when
both are empty; empty text is not sent to the model.

Semantic similarity is used for free-form text: the summary, decision
descriptions, and `action` values. A text is considered semantically
correct when its cosine similarity is at least the configured threshold
(`0.65` by default). The default is the midpoint of the moderate-similarity
band (`0.5` to `0.8`): `(0.5 + 0.8) / 2 = 0.65`. This makes the cutoff a
moderate-similarity acceptance criterion, rather than requiring strong
similarity. It is a chosen operational threshold, not an empirically measured
average or a probability of correctness; use `--threshold` to choose another
cutoff when appropriate.

The following ranges are qualitative guidance for interpreting cosine scores,
not universal guarantees of semantic correctness:

| Score | Interpretation |
| --- | --- |
| `+1.0` | Identical direction (maximum similarity) |
| `0.8 ≤ score < 1.0` | Strong similarity |
| `0.5 ≤ score < 0.8` | Moderate similarity |
| `0.0 < score < 0.5` | Weak positive similarity |
| `0.0` | Orthogonal vectors (no directional similarity) |
| `-1.0 < score < 0.0` | Opposite-direction similarity |
| `-1.0` | Opposite directions (maximum dissimilarity) |

## Accuracy
Exact accuracy is used for structured fields: owners are compared after
lower-casing and collapsing whitespace, while due dates are compared as exact
values, including `null`. Similarity is not used to accept an approximate
owner or date.

## Extraction metrics

Decisions and actions are matched one-to-one. A decision matches when its
description reaches the threshold. An action additionally requires exact,
normalized owner and exact due date (including correct `null` values).

For each category, the report contains true positives (`TP`), false positives
(`FP`), false negatives (`FN`), precision, recall, and F1:

- `Precision = TP / (TP + FP)`
- `Recall = TP / (TP + FN)`
- `F1 = 2 * Precision * Recall / (Precision + Recall)`

When both the expected and predicted collections are empty, `TP`, `FP`, and
`FN` are reported as `null` because no items were evaluated. This is treated as
a correct empty result, so precision, recall, and F1 are each `1.0`.

`TP` counts a predicted item matched to one expected item. Matching is
one-to-one, so an expected item cannot be matched more than once. `FP` counts
extra predicted items, and `FN` counts expected items with no match. A decision
match requires only semantic similarity above the threshold. An action match
requires all three conditions: semantic similarity of the action text above
the threshold, an exact normalized owner match, and an exact due-date match.

## Response metrics

- **Average Summary Similarity:** mean embedding cosine similarity across all
  cases; this is a graded metric from `0` to `1`, not a pass/fail count.
- **Summary Semantic Correctness Rate:** proportion of cases whose summary
  similarity is at or above the configured threshold.
- **Owner accuracy:** one-to-one exact normalized owner matches divided by the
  number of expected actions. If a case has no expected actions, its accuracy
  is `1.0`.
- **Due-date accuracy:** one-to-one exact due-date matches divided by the
  number of expected actions; a correct `null` is an exact match. If there are
  no expected actions, its accuracy is `1.0`.
- **Schema validation rate:** proportion of responses with a string `summary`,
  a list of string `decisions`, and a list of correctly shaped `actions`.
- **Fully Passing:** a case is fully passed only when its schema is valid, its
  summary meets the threshold, and both decisions and actions have zero
  false positives and zero false negatives. Owner and due-date correctness is
  enforced as part of action matching.

In other words, a response is not `fully_passed` merely because its summary is
similar or its extraction F1 is high: every expected decision and action must
be matched, no extra items may be present, and the response must satisfy the
schema.

## CSV report columns

`results/evaluation_report.csv` contains one row per evaluation case. The columns
have the following meanings:

| Column | Meaning |
| --- | --- |
| `id` | Identifier of the evaluation case. |
| `summary_similarity` | Cosine similarity between the expected and predicted summaries, from `0` to `1`. |
| `summary_correct` | Whether `summary_similarity` meets the configured threshold. |
| `decision_tp` | Number of expected decisions matched by a predicted decision. |
| `decision_fp` | Number of predicted decisions that do not match an expected decision. |
| `decision_fn` | Number of expected decisions that were not predicted. |
| `decision_precision` | Decision precision: `TP / (TP + FP)`. |
| `decision_recall` | Decision recall: `TP / (TP + FN)`. |
| `decision_f1` | Harmonic mean of decision precision and recall. |
| `action_tp` | Number of expected actions matched by a predicted action with matching `action`, owner, and due date. |
| `action_fp` | Number of predicted actions whose `action`, owner, or due date does not match an expected action. |
| `action_fn` | Number of expected actions that were not predicted correctly. |
| `action_precision` | Action precision: `TP / (TP + FP)`. |
| `action_recall` | Action recall: `TP / (TP + FN)`. |
| `action_f1` | Harmonic mean of action precision and recall. |
| `owner_accuracy` | Proportion of expected actions with a one-to-one predicted owner match after normalization. |
| `due_date_accuracy` | Proportion of expected actions with a one-to-one predicted due-date match, including `null`. |
| `schema_valid` | Whether the prediction has the required fields and value types. |
| `fully_passed` | Whether the case passes schema, summary, decision, and action checks. |
| `failure_reason` | Semicolon-separated explanation of any failed checks; empty when all checks pass. |

Empty collections are handled safely. Failed cases are listed in the CSV with
their reason, and fully passing cases are kept separate from extraction F1.
