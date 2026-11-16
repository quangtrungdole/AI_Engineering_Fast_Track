# Weekly Submission – W01 / Member dlqtrung

**Feature (F01–F04 or Foundation):** Foundation — prompt-based issue classification

**What I studied (2–3 concepts):**

1. **Generative AI, LLMs, and prompts:** The Microsoft Learn module introduces
   how generative AI applications use large language models and prompts to
   create content and complete tasks. I applied this by sending the 20 issue
   texts to an OpenAI model with a task-specific classification prompt.
   [Microsoft Learn: Introduction to generative AI and agents](https://learn.microsoft.com/en-us/training/modules/fundamentals-generative-ai/)
2. **Clear instructions and constrained output:** The DeepLearning.AI prompt
   engineering course covers practical prompt design for application tasks,
   including specifying the task, rules, and expected output. I applied this
   by defining the four categories, three priorities, required fields, valid
   values, and JSON-only response format in `prompt_v1.md`.
   [DeepLearning.AI: ChatGPT Prompt Engineering for Developers](https://learn.deeplearning.ai/courses/chatgpt-prompt-eng/lesson/dfbds/introduction)
3. **Iterative prompt development and evaluation:** I compared prompt versions
   against the gold labels and refined the priority rules. V2 strengthened
   critical P1 detection; V3 added explicit P2/P3 guidance for operational
   reporting, reporting cadence, incident governance, and workflow changes.
   This follows the course's iterative approach to improving prompt results.
   [DeepLearning.AI course overview](https://www.deeplearning.ai/alpha/short-courses/chatgpt-prompt-engineering-for-developers)

**What I built (summary + key modules):**

- [`assignments/w01/classify_issues.py`](../assignments/w01/classify_issues.py)
  - Loads the 20 issue records from `issue_classification_gold.json`.
  - Sends only `issue_id` and `text` to the model; gold `category` and
    `priority` values are excluded from the prompt.
  - Sends all issues in one OpenAI request.
  - Validates the JSON response with Pydantic using fixed category and priority
    values and a required `next_action`.
  - Writes evaluator-compatible CSV output.
- [`assignments/w01/prompts/prompt_v1.md`](../assignments/w01/prompts/prompt_v1.md),
  [`prompt_v2.md`](../assignments/w01/prompts/prompt_v2.md), and
  [`prompt_v3.md`](../assignments/w01/prompts/prompt_v3.md) contain three
  iterations of the classification prompt.
- `assignments/w01/results/` stores the prediction CSV for each prompt version.
- `scripts/evaluate_issue_classifier.py` compares predictions with the gold
  labels and reports category accuracy, priority accuracy, and P1 misses.

**How to run:**

From the repository root, configure `OPENAI_API_KEY` in `.env`, then run:

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

Evaluate each output:

```bash
python scripts/evaluate_issue_classifier.py \
  assignments/w01/results/issue_predictions_v1.csv
python scripts/evaluate_issue_classifier.py \
  assignments/w01/results/issue_predictions_v2.csv
python scripts/evaluate_issue_classifier.py \
  assignments/w01/results/issue_predictions_v3.csv
```

**Results:**

| Prompt version | Category accuracy | Priority accuracy | Critical P1 misses |
|---|---:|---:|---|
| V1 | 20/20 (100%) | 16/20 (80%) | CASE-16 |
| V2 | 20/20 (100%) | 16/20 (80%) | None |
| V3 | 20/20 (100%) | 20/20 (100%) | None |

**Known failures / trade-offs:**

- V1 and V2 showed that category classification was reliable while priority
  boundaries required more explicit rules and examples.
- The model response depends on the selected model, prompt version, and API
  configuration; rerunning may produce different results.
- All 20 issues are sent in one request, which keeps the task consistent but
  increases prompt size and makes the run dependent on one batch response.
- The evaluation uses public synthetic fixtures. Hidden assessment cases may
  expose additional priority ambiguities.

**Demo link:**
None

**PR link:** 
https://github.com/quangtrungdole/AI_Engineering_Fast_Track/pull/1

**Next action:**
Prepare for the Week 2 assignment by reviewing the next requirements and
acceptance criteria, preserving the W01 evaluation workflow, and identifying
which W01 components can be reused. Carry forward the prompt versioning,
structured response validation, CSV evaluation, and error-handling practices
into the Week 2 implementation.
