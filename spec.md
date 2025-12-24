# AI Consensus CLI - Ideation Spec (Draft)

## Goal
Build a CLI that sends a user prompt to multiple AI models, gathers their responses, iteratively shares critiques, and returns a consensus answer.

## High-Level Flow
1) User prompt -> send to N models
2) Collect responses
3) Share a summarized digest of others' responses to each model
4) Each model returns: agreement, objections, and suggested edits
5) A mediator (or structured voting) produces a revised candidate answer
6) Repeat until convergence or stop conditions

## Proposed Protocol (Baseline)
- Use a mediator loop:
  - Round 1: participants answer the prompt
  - Round 2+: mediator synthesizes -> participants approve/criticize -> mediator updates
- Consensus criteria:
  - Majority approval (>= 2/3) AND no critical objections
- Stop conditions:
  - Max rounds: 3
  - Early stop: low delta in mediator output or consensus criteria met

## Defaults (Recommended)
- Models: gpt-4o, claude-3-5, gemini-1.5
- Mediator: gpt-4o (can be configurable later)
- Audit trail: off by default; enable with --verbose
- Share mode: summarized digest (not raw peer responses)
- Weights: equal weights across models
- Confidence: optional; captured when supported, but not required for consensus
- Convergence fallback: if no consensus by max rounds, return best candidate + disagreement summary

## Consensus Algorithm (Full Draft)
1) Round 1: collect independent answers from all participants.
2) Mediator builds a candidate_answer and rationale:
   - Extract common claims
   - Identify conflicts and missing points
   - Draft a unified answer that resolves conflicts where possible
3) Build a digest for participants:
   - Common points across answers
   - Top 3 objections (by frequency or severity)
   - Top 3 missing items
   - Suggested edits with short labels
4) Round 2+ participant feedback:
   - Provide candidate_answer + digest
   - Each participant returns a critique object
5) Mediator updates candidate_answer using critiques.
6) Consensus reached if:
   - approvals >= ceil(2/3 * participants)
   - AND critical objections == 0
7) Stop rules:
   - Max rounds: 3
   - Early stop if candidate_answer changes < 10% (measured by token diff or length delta)
8) If no consensus at stop:
   - Return best candidate_answer
   - Attach disagreement summary (brief)

## Digest Format (Full Draft)
- common_points: bullet list, 3-7 items
- objections: bullet list, 1-5 items
- missing: bullet list, 1-5 items
- suggested_edits: bullet list with short labels

## Response Schema (Draft)
Each model returns:
- answer: string
- approve: bool (if round > 1)
- critical: bool (if round > 1)
- objections: list of strings
- missing: list of strings
- edits: list of patch-style suggestions or bullet points
- confidence: float (0-1, optional)

Mediator returns:
- candidate_answer: string
- rationale: short summary of major changes
- approval_count: int
- critical_objections: list
- disagreement_summary: short summary (only if no consensus)

## Open Questions
- Which models are required in v1?
- Does the user want an audit trail by default or only with a flag?
- Should models see raw peer responses or a summarized digest?
- Should there be a judge model, or only participants + mediator?
- How to handle persistent disagreement (pick best answer vs return multiple)?

## Non-Goals (v1)
- Long-term memory or per-user personalization
- Web browsing or tool-use by the models
- Domain-specific compliance features

## CLI UX (Sketch)
- Run:
  - aicx "your prompt"
- Flags:
  - --models gpt-4o,claude-3-5,gemini-1.5
  - --rounds 3
  - --verbose (print audit trail)

## Risks
- Token growth across rounds
- False consensus on incorrect answers
- Oscillation or stalling without convergence

## Next Steps
- Finalize protocol and stop rules
- Define internal data structures
- Build CLI scaffold and config format
