# Prompt Contracts

## General Principles
- Prompts must be deterministic and explicit about format.
- Each prompt includes the required response schema.
- Use stable labels for fields to simplify parsing.

## Participant Prompt (Round 1)
System instruction (template):
- Role: Provide the best possible answer to the user prompt.
- Output schema: a JSON object with fields:
  - answer: string
  - confidence: float (optional, 0-1)

User message:
- The user prompt string.

## Participant Critique Prompt (Round 2+)
System instruction (template):
- Role: Critique the candidate answer.
- Output schema:
  - approve: bool
  - critical: bool
  - objections: list[string]
  - missing: list[string]
  - edits: list[string]
  - confidence: float (optional)
 - critical criteria:
   - Mark critical true only for factual errors or advice that could cause harm.
   - Do not mark critical for style or minor omissions.

User message:
- candidate_answer
- digest

## Mediator Synthesis Prompt
System instruction (template):
- Role: Synthesize a candidate answer based on participant responses.
- Output schema:
  - candidate_answer: string
  - rationale: string
  - common_points: list[string]
  - objections: list[string]
  - missing: list[string]
  - suggested_edits: list[string]

Input:
- All participant answers.
- Optional: critique feedback in later rounds.

## Mediator Update Prompt (Round 2+)
System instruction (template):
- Role: Update candidate_answer using critiques.
- Output schema:
  - candidate_answer: string
  - rationale: string

Input:
- candidate_answer
- All critique responses

## Parsing Strategy
- Expect strict JSON output. Reject or retry on malformed output.
- If strict parsing fails, attempt a limited recovery:
  - Extract JSON from a fenced ```json code block if present.
  - Extract the first JSON object in the response.
  - If still invalid, record error and mark response as failed.
- If `strict_json` is enabled, disable recovery and fail on first parse error.

## Provider Notes
- Use native JSON modes where available (OpenAI, Gemini).
- Prompts may be tuned per provider to maximize JSON compliance.
