# W01 Issue Classification — Prompt V1

Classify every issue in the JSON array provided after this instruction.

## Category rules

- `Bug`: something is currently broken, failing, or behaving incorrectly.
- `Feature`: a requested capability, change, or enhancement.
- `Question`: a request for information or clarification.
- `Risk`: a possible future problem, delay, outage, or failure that has not happened yet.

## Priority rules

- `P1`: widespread current impact or an imminent serious production/release risk.
- `P2`: meaningful impact or a material risk that needs planned attention.
- `P3`: low-impact work, a general question, or a minor improvement.

## Output requirements

Return only a valid JSON array with exactly one object for every input issue.
Do not include Markdown fences, explanations, or additional keys. Preserve each
input `issue_id` exactly. Each object must have this shape:

```json
{
  "issue_id": "CASE-01",
  "category": "Bug",
  "priority": "P1",
  "next_action": "Investigate the production failure and begin incident response."
}
```

`category` must be one of `Bug`, `Feature`, `Question`, or `Risk`.
`priority` must be one of `P1`, `P2`, or `P3`.
`next_action` must be a concise, practical action for the delivery team.
