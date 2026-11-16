# W01 Issue Classification — Prompt V3

Classify every issue in the JSON array provided after this instruction.
Evaluate each issue independently and preserve its `issue_id` exactly.

## Category rules

- `Bug`: something is currently broken, failing, or behaving incorrectly.
- `Feature`: a requested capability, change, or enhancement.
- `Question`: a request for information or clarification.
- `Risk`: a possible future problem, delay, outage, or failure that has not happened yet.

## Priority rules

Assign priority from the issue's actual impact and consequence. Do not infer
priority from category alone. A feature can be P2 or P3, and a question can be
P2 or P3.

### P1 — critical

Use `P1` when at least one of these conditions is true:

1. A production or business-critical capability is already unavailable for
   all users, all customers, or a broad population.
2. A critical transaction or service, such as payment processing, checkout,
   login, data access, data export, or reporting, is failing globally or
   blocks the primary user flow.
3. A production API, endpoint, or service returns errors for all users or all
   customers. This includes HTTP 5xx failures such as an export endpoint
   returning `500` for every customer, even when the affected capability is
   not the primary checkout or login flow.
4. A security, identity, or authentication failure prevents users from
   accessing the system or creates an imminent serious production risk.
5. A security or compliance dependency will expire or fail before go-live and
   would block release or create a serious exposure.
6. A critical external dependency has no fallback or recovery path, and its
   outage would prevent production access or a primary business flow.

Words such as `may`, `could`, or `risk` do not automatically make an issue
P2. If the consequence is a broad outage, serious security exposure, release
blocker, or loss of a critical fallback, use `P1` even if the failure has not
happened yet.

### P2 — significant or operationally important

Use `P2` when the issue needs planned attention because it affects delivery
operations, governance, reporting, or an important workflow, but it does not
meet the P1 conditions.

Classify the following as P2:

- A requested change to operational reporting, such as adding project or
  tracking data to a status report.
- A change to reporting cadence or monitoring frequency that materially
  affects delivery visibility, such as moving from weekly to daily reporting.
- A question about incident governance, ownership, approval, escalation, or
  sign-off responsibilities.
- A vendor or dependency risk that may delay delivery but has no stated
  broad-outage, security, or no-fallback condition.
- A bug that causes incorrect behavior in a working workflow but does not
  block the primary flow for a broad population.

The important distinction is whether the issue changes how the team operates,
governs incidents, or maintains delivery visibility. These are P2 even when
the wording does not mention an outage or deadline.

### P3 — low urgency or convenience

Use `P3` for work that is useful but low urgency and does not materially affect
delivery operations or governance. Examples include:

- Cosmetic presentation changes such as a dark theme.
- Convenience controls such as a download button.
- A general export option that is not described as necessary for operational
  reporting, compliance, or a release decision.
- Routine factual lookups about dates, counts, storage locations, or hosting
  details when no urgent consequence is stated.

Do not promote a feature to P2 merely because it is a new feature. Do not
demote an operational reporting, cadence, approval, or governance request to
P3 merely because it is phrased as a small change or a question.

## Priority decision procedure

For every issue, check these rules in order:

1. Is a critical user or business flow broadly unavailable now? If yes, use
   `P1`.
2. Does any production API, endpoint, or service return an error for all
   customers or users? If yes, use `P1`, including a universal error on
   data export or reporting.
3. Is there an imminent security, identity, compliance, or release-blocking
   failure? If yes, use `P1`.
4. Is a critical dependency a single point of failure with no fallback? If
   yes, use `P1`.
5. Does the issue affect operational reporting, reporting cadence, incident
   approval, ownership, escalation, sign-off, or another important delivery
   workflow? If yes, use `P2`.
6. Is it a meaningful but non-critical bug, feature, or delivery risk? If yes,
   use `P2`.
7. Otherwise, use `P3`.

When several rules appear applicable, choose the highest priority. Never
downgrade a P1 issue because it is written as a future risk. Use the issue's
described impact rather than guessing an unrelated impact.

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
