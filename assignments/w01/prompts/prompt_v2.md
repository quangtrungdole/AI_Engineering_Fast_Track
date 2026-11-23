# W01 Issue Classification — Prompt V2

Classify every issue in the JSON array provided after this instruction.
Evaluate each issue independently and preserve its `issue_id` exactly.

## Category rules

- `Bug`: something is currently broken, failing, or behaving incorrectly.
- `Feature`: a requested capability, change, or enhancement.
- `Question`: a request for information or clarification.
- `Risk`: a possible future problem, delay, outage, or failure that has not happened yet.

## Priority rules

Assign priority based on impact, urgency, scope, and the possibility of a
serious production or release failure. Do not assign priority based only on
whether the issue is phrased as a question, feature request, or risk.

### P1 — critical

Use `P1` when a production-wide or broad user impact causes critical service disruption, 
blocks primary business flows (e.g., payment, login, data access, or export), 
causes global API failures, creates serious security or compliance exposure, 
blocks go-live, or involves a critical dependency with no fallback.

Words such as `may`, `could`, or `risk` do not automatically make an issue
P2. If the consequence is a broad outage, serious security exposure, release
blocker, or loss of a critical fallback, use `P1` even if the failure has not
happened yet.

### P2 — significant

Use `P2` when the issue needs timely planned attention but does not meet the
P1 conditions. Examples include a meaningful feature, an important operational
question, a vendor dependency that may delay delivery but has mitigation, or a
moderate release risk.

### P3 — low urgency

Use `P3` for low-impact improvements, cosmetic work, routine information
requests, and issues with no immediate or material delivery risk.

## Priority decision procedure

For every issue, check the following in order:

1. Is a critical user or business flow broadly unavailable now? If yes, use
   `P1`.
2. Does any production API, endpoint, or service return an error for all
   customers or users? If yes, use `P1`, including a universal error on
   data export or reporting.
3. Is there an imminent security, identity, compliance, or release-blocking
   failure? If yes, use `P1`.
4. Is a critical dependency a single point of failure with no fallback? If
   yes, use `P1`.
5. Otherwise, does the issue require meaningful near-term attention? If yes,
   use `P2`.
6. Otherwise, use `P3`.

Do not downgrade a P1 issue merely because it is written as a future risk or
does not explicitly say the word `production`. Focus on the described impact
and consequence.

## Output requirements

Return only a valid JSON array with exactly one object for every input issue.
Do not include Markdown fences, explanations, or additional keys. The output
must contain the same set of issue IDs as the input, exactly once each.

Each object must have this shape:

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
