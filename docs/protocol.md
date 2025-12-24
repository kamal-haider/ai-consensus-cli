# Consensus Protocol

## Phases
- Initialization: load config, validate models, set round limits.
- Round 1: independent answers from all participants.
- Synthesis: mediator produces candidate answer and rationale.
- Critique: participants review candidate, respond with structured feedback.
- Update: mediator revises candidate and updates summary stats.
- Stop: consensus criteria met or stop conditions reached.

## Round 1: Independent Answers
Input to each participant:
- The user prompt.
- A fixed system instruction describing the role and response schema.

Output:
- A Response object with an `answer` plus optional `confidence`.

## Digest Construction
After Round 1, the mediator produces a digest to share with participants:
- common_points: shared claims across answers.
- objections: notable conflicts or contradictions.
- missing: key points absent in most answers.
- suggested_edits: concise fix labels (not full patches).

## Round 2+ Critique
Input to each participant:
- The candidate answer.
- The digest from the mediator.
- A fixed critique instruction and response schema.

Output:
- approve: bool
- critical: bool
- objections: list
- missing: list
- edits: list
- optional confidence

## Mediator Update
The mediator consumes all critiques and updates:
- candidate_answer
- rationale
- approval_count
- critical_objections

## Output
If consensus is reached:
- Return candidate_answer and rationale (optional, verbose only).

If no consensus by stop conditions:
- Return candidate_answer and disagreement_summary.

## Idempotency
- Given the same prompt, model configs, and provider outputs, the loop yields the same result.

## Role Separation
- The mediator is not a participant in v1 and does not contribute an independent answer.
