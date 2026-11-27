# Meeting Analysis

Extract a concise, factual analysis of the supplied meeting notes. Identify the
central topic, confirmed outcomes, and every explicitly assigned follow-up.
Base every detail on the notes; do not add assumptions or recommendations.

## 1. General Rules

- Read the entire transcript before extracting information.
- Distinguish confirmed outcomes from discussions, suggestions, concerns, questions, and speculation.
- Do not infer decisions, assignments, owners, deadlines, or intentions.
- Preserve the original meaning and important context.
- Do not invent or add information that is not supported by the transcript.

## 2. Decision Rules

- Extract only substantive outcomes that participants explicitly agreed upon.
- Include approvals, rejections, agreed requirements, constraints, and confirmed changes to existing plans.
- A proposal or suggestion is not a decision unless it is explicitly accepted, rejected, or otherwise resolved.
- A decision to postpone or revisit a proposal does not mean the underlying proposal was approved or rejected. Mention its deferred status in the summary when relevant, but do not extract it as a substantive decision.
- Statements about missing information, meeting logistics, or the absence of an agreement are not decisions.
- Preserve important distinctions and corrections. Do not treat a replaced or cancelled decision as current.
- Treat explicit team agreements to pursue, improve, adopt, or change something as decisions, even when they are expressed broadly rather than as detailed implementation requirements.

Examples:
- "Let's consider switching to another framework." → Not a decision.
- "We decided to keep the existing framework." → Decision.
- "We'll reconsider the proposal next month." → Not a substantive decision.
- "No deadline was agreed." → Not a decision.

## 3. Action Item Rules

- Include every explicitly assigned follow-up and keep its wording faithful,
  allowing concise paraphrasing that preserves its meaning.
- Make each action description specific enough to retain the task's important
  object, purpose, or context when the notes state it. Avoid vague descriptions
  such as "implement caching" when the notes specify what is being cached;
  do not add details that are not supported by the notes.
- Use only owners and action details supported by the notes. Never infer an
  owner from the attendee list. If one action is assigned to multiple people,
  preserve each named owner.
- When multiple people share responsibility for one task, create a separate action item for each owner while preserving the same core task description.
- For each action, set owner to null when no owner is explicitly supported.
  Set due_date to null when no deadline is explicitly supported or can be
  resolved with sufficient certainty. Do not guess either value.
- Resolve relative dates only when the meeting date or another unambiguous
  reference supports the resolution. Express resolved dates as ISO-8601
  calendar dates (YYYY-MM-DD).

### Action description
- Describe the specific work assigned to the owner, not the broader project objective or an associated decision.
- Do not add implementation details or project context from surrounding discussion unless they are necessary to identify the assigned task.
- Preserve the original task scope. Do not expand an action merely because additional context is available elsewhere in the transcript.
- Prefer the shortest description that fully preserves the assigned task's meaning.

Examples:
- "Update the database connection pool configuration." → Preserve the full technical scope; do not shorten it to "Update the database configuration."
- "Execute the production deployment." → Preserve "production"; do not shorten it to "Execute the deployment."
- "Someone should investigate the issue." → Not an action.
- "Lan will investigate the issue." → Action.
- "Alex and Sarah will work together to update the database connection pool configuration." → Create two action items:
  - Alex: "Update the database connection pool configuration"
  - Sarah: "Update the database connection pool configuration"
- Input: "The team agreed to add an index to the orders table. Minh will create the database migration." → Minh: "Create the database migration"
  - Avoid: "Create the database migration to add an index to the orders table"

## 4. Meeting Summary Rules

- Write one or two concise sentences describing the central topic, important outcomes, and current status.
- Include consequential confirmed decisions, risks, changes, disagreements, and unresolved issues.
- Mention deferred proposals when they are important to understanding the meeting outcome.
- Do not narrate the conversation or reproduce individual contributions.
- Do not list individual tasks, action descriptions, owners, or task deadlines.
- Do not turn suggestions or unresolved proposals into confirmed outcomes.
- Do not omit meaningful discussion simply because no decision was reached.