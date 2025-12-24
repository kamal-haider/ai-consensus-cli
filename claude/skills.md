# AI Consensus CLI - Claude Skills Reference

This document is Claude's source of truth for the AI Consensus CLI project. All specifications below are authoritative and should be followed exactly.

---

# Overview

## Goal
Deliver a command-line tool that submits a user prompt to multiple AI models, gathers independent answers, runs structured critique rounds, and returns a final consensus response. The process should be deterministic by default, auditable when requested, and configurable without hidden magic.

## Non-Goals (v1)
- Web browsing or tool use by models.
- Long-term memory or personalization.
- Domain-specific compliance or policy enforcement.
- Streaming token-level collaboration.

## Guiding Principles
- Determinism by default: stable output given the same inputs and model configs.
- Explicitness over clever abstractions.
- Small, reviewable changes.
- Clean default output, with verbose audit trails only when requested.

## Assumptions
- Providers expose chat completion APIs.
- A single CLI invocation runs a full consensus cycle and exits.
- Failures for individual models are tolerated when possible.
- The CLI runs without network access unless the user provides credentials and allows it.

## User Stories
- As a user, I can ask a question and receive a consensus answer that explains any key disagreements.
- As a developer, I can add a model provider by implementing a small adapter and config.
- As an operator, I can enable a verbose audit trail for debugging and compliance.

## Success Criteria
- Consensus loop completes in <= 3 rounds for typical prompts.
- Deterministic ordering and aggregation of responses.
- Clear failure messages when consensus cannot be reached.
- Easy to extend to new models.

---

# Architecture

## Components
- CLI Frontend: parses args, loads config, triggers consensus loop.
- Orchestrator: coordinates rounds, model calls, and mediator steps.
- Provider Adapters: per-model API wrappers with a common interface.
- Consensus Engine: implements aggregation, critique processing, and stop logic.
- Audit Logger: optional verbose trace of inputs/outputs.

## Data Flow
1) CLI reads config, merges with CLI overrides.
2) Orchestrator initializes participant list and mediator.
3) Round 1: participants answer independently.
4) Mediator builds candidate answer and digest.
5) Rounds 2+: participants critique candidate; mediator updates.
6) Consensus engine checks stop criteria.
7) Output final candidate and disagreement summary.

## Module Responsibilities (Proposed)
- src/aicx/__main__.py
  - CLI entrypoint, argument parsing, exit codes.
- src/aicx/config.py
  - Load/merge configuration, validation.
- src/aicx/models/
  - Provider adapters and registry.
- src/aicx/consensus/
  - Consensus loop, digest creation, stop logic.
- src/aicx/prompts/
  - Prompt templates and rendering.
- src/aicx/logging.py
  - Verbose audit output and redaction.
- src/aicx/types.py
  - Dataclasses and shared schemas.

## Determinism
- Stable sorting of participants by name and version.
- Stable ordering of critiques and digest items.
- If randomization is added later, seed must be explicit.

## Extensibility
- Providers are pluggable via a registry.
- Prompt templates are versioned and referenced by name.
- Consensus criteria can be swapped via configuration.

## Boundary Decisions
- No caching in v1.
- No parallelization required in v1 (optionally can be added later).
- No tool-use or function-calling in v1.

---

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

---

# Consensus Algorithm

## Criteria
Consensus is reached when both of the following hold:
- approvals >= ceil(2/3 * participants)
- critical_objections == 0

## Stop Conditions
- Max rounds reached (default: 3 total rounds).
- Early stop if candidate changes below threshold.
- Early stop if no changes proposed by any participant.

## Change Threshold
- Use a deterministic diff metric.
- Recommended: normalized Levenshtein distance on whitespace-tokenized text (split on `\s+`).
- Default threshold: < 10% change.

## Disagreement Summary
If consensus is not reached, include:
- Top 3 unresolved objections.
- Any remaining missing items.
- A short note explaining why consensus failed.

## Scoring (Optional, v1 default off)
- Weighted approvals by model weight.
- Weighted objection severity.

## Edge Cases
- If a participant fails to respond, proceed if quorum is met.
- If quorum not met, abort with a clear error.

## Quorum
- Default quorum: ceil(2/3 * participants).
- Configured participants must be >= 2.
- Quorum behavior is configurable.

## Critical Objections
- A critical objection is one that indicates factual error or potential harm, as defined in prompt criteria.

---

# Data Models

Use Python dataclasses for shared data between stages. This document defines logical schemas; actual types live in `src/aicx/types.py`.

## Core Types

### ModelConfig
- name: string
- provider: string
- model_id: string
- temperature: float
- max_tokens: int
- timeout_seconds: int
- weight: float

### RunConfig
- models: list[ModelConfig]
- mediator: ModelConfig
- max_rounds: int
- quorum: int
- approval_ratio: float
- change_threshold: float
- max_context_tokens: int | None
- strict_json: bool
- verbose: bool
- share_mode: string (digest|raw)

### PromptRequest
- user_prompt: string
- system_prompt: string
- round_index: int
- role: string (participant|mediator)
- input_digest: Digest | None
- candidate_answer: string | None

### Response
- model_name: string
- answer: string
- approve: bool | None
- critical: bool | None
- objections: list[string]
- missing: list[string]
- edits: list[string]
- confidence: float | None
- raw: string | None (if needed for audit)

### Digest
- common_points: list[string]
- objections: list[string]
- missing: list[string]
- suggested_edits: list[string]

### MediatorState
- candidate_answer: string
- rationale: string
- approval_count: int
- critical_objections: list[string]
- disagreement_summary: string | None

## Serialization Rules
- All objects are JSON-serializable.
- Use ASCII output by default unless a model returns Unicode.
- Stable key ordering for deterministic logs.

## Validation Rules
- `approval_ratio` in [0, 1].
- `change_threshold` in [0, 1].
- `max_rounds` >= 1.
- `weight` >= 0.

## Parsing Defaults
- Missing optional fields in model responses default to empty lists or None.
- Extra fields are ignored unless explicitly supported.

---

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

---

# Configuration

## Location
- Default: `config/config.toml`
- Override with `--config`.

## Format (TOML)

Example:

```toml
[run]
max_rounds = 3
approval_ratio = 0.67
change_threshold = 0.10
share_mode = "digest"
max_context_tokens = 12000
strict_json = false
verbose = false

[[model]]
name = "gpt-4o"
provider = "openai"
model_id = "gpt-4o"
temperature = 0.2
max_tokens = 2048
timeout_seconds = 60
weight = 1.0

[[model]]
name = "claude-3-5"
provider = "anthropic"
model_id = "claude-3-5-sonnet-20241022"
temperature = 0.2
max_tokens = 2048
timeout_seconds = 60
weight = 1.0

[mediator]
name = "gpt-4o"
provider = "openai"
model_id = "gpt-4o"
```

## Notes
- `name` is a friendly alias used in CLI and logs.
- `model_id` is the provider-specific identifier passed to the API.
- If `max_context_tokens` is set, older rounds should be summarized to stay within budget.
- `strict_json` disables JSON recovery and fails on any malformed output.

## Resolution Order
1) Defaults baked into code.
2) Config file values.
3) CLI overrides.

## Validation
- All model names must be unique.
- Mediator must reference a configured model and must not appear in the participant list.
- If a model entry is missing required fields, fail fast.

## Secrets
- API keys are read from environment variables.
- No secrets in config files.

---

# Provider Adapters

## Interface Contract
Each provider adapter implements:
- name: provider identifier
- supports_json: bool
- create_chat_completion(request: PromptRequest) -> Response

## Adapter Responsibilities
- Map PromptRequest into provider-specific API calls.
- Enforce timeout and max_tokens.
- Return a Response with the `raw` field when verbose is enabled.

## Error Mapping
- Network errors -> ProviderError.
- Timeout -> ProviderError with code "timeout".
- Malformed output -> ParseError.

## Environment Variables
- OPENAI_API_KEY
- ANTHROPIC_API_KEY
- GEMINI_API_KEY

## Model Names and Aliases
- `name` is a friendly alias (used in CLI and logs).
- `model_id` is passed to the provider API.
- The system should accept a small alias table and pass through unknown names verbatim.

Alias table (initial):
- gpt-4o -> gpt-4o
- claude-3-5 -> claude-3-5-sonnet-20241022
- gemini-1.5-pro -> gemini-1.5-pro
- gemini-1.5-flash -> gemini-1.5-flash

## JSON Mode Support
- OpenAI: response_format json_object
- Gemini: response_mime_type application/json
- Anthropic: prompt-only JSON compliance

## Rate Limiting
- No global limiter in v1.
- Adapters should surface rate limit errors clearly.

## Deterministic Settings
- temperature default 0.2.
- set top_p = 1.0 where supported to reduce sampling variance.
- top_p, frequency_penalty, and other params unset unless configured.

---

# CLI Interface

## Command
- aicx "your prompt"

## Flags
- --models: comma-separated list of model identifiers
- --mediator: model identifier
- --rounds: max number of rounds (default 3)
- --approval-ratio: fraction for consensus (default 0.67)
- --change-threshold: early stop threshold (default 0.10)
- --max-context-tokens: soft cap for total context; triggers summarization
- --verbose: enable audit trail
- --config: path to config file
- --share-mode: digest|raw
- --strict-json: disable JSON recovery and fail on first parse error
- --no-consensus-summary: omit disagreement summary

## Output
- Standard output: final candidate answer only.
- Standard error (verbose mode only): structured logs and diagnostics.

## Exit Codes
- 0: success (consensus or fallback).
- 1: configuration error.
- 2: provider error or zero successful responses.
- 3: consensus loop failed due to quorum with partial responses.
- 4: internal error.

## Performance and Cost (Estimates)
- Typical run (3 models, 2 rounds): ~20-40s, roughly $0.10-$0.30.
- Longer run (3 models, 3 rounds): ~40-60s, roughly $0.20-$0.50.
- Costs vary by model selection and response length.

## Examples
- aicx "Explain Rust ownership"
- aicx "Summarize this text" --models gpt-4o,claude-3-5 --rounds 2

---

# Error Handling

## Principles
- Fail fast on configuration errors.
- Continue on individual model failures when quorum is met.
- Produce actionable error messages.

## Failure Modes
- ConfigError: invalid or missing config values.
- ProviderError: API failures, timeouts, invalid credentials.
- ParseError: malformed model output.
- QuorumError: insufficient successful responses.
- InternalError: unexpected exceptions.

## Retries
- No retries by default.
- Optional retries in config with exponential backoff (future).

## Timeouts
- Provider calls must respect `timeout_seconds`.
- Timeout counts as a failed response.

## Partial Failures
- If a participant fails, continue if quorum is satisfied.
- If mediator fails, abort.

## Zero Successful Responses
- If all participants fail, abort immediately with a ProviderError.
- The error message should enumerate failures per model.
- Exit code should be 2 for zero responses, 3 for below-quorum with some responses.

---

# Logging and Audit Trail

## Default Behavior
- No logs by default.
- Only the final consensus answer is printed to stdout.

## Verbose Mode
- Enabled with `--verbose`.
- Logs are written to stderr as structured JSON lines.
- Each line includes `event`, `timestamp`, `round`, `model`, and `payload`.

## Redaction
- User prompt is logged as plain text in verbose mode.
- Provider credentials are never logged.
- Model raw responses can be stored if `verbose` is enabled.

## Events
- config_loaded
- round_started
- model_request
- model_response
- parse_recovery_attempt
- context_truncated
- mediator_update
- consensus_check
- run_complete
- error

## Retention
- The CLI does not write to disk by default.
- Users can pipe stderr to files when needed.

---

# Runtime Behavior

## Execution Model
- Single-process CLI.
- Provider calls can be sequential in v1.
- Optional parallel execution can be added later.

## Ordering
- Participants are processed in stable sorted order by name.
- Mediator is always invoked after all participant responses are collected.

## Resource Limits
- Max rounds: default 3.
- Max tokens per model: config-driven.
- Timeout per call: config-driven.
- Max context tokens: config-driven; truncate oldest rounds when near limit (v1).

## Context Limit Behavior (v1)
- If context exceeds `max_context_tokens`, truncate oldest round content first.
- Log a warning event in verbose mode when truncation occurs.

## Determinism Notes
- If parallel execution is introduced, results must be re-sorted before aggregation.
- Any use of randomness must be seeded by config.

---

# Security and Safety

## Threat Model
- Prompt injection within user input.
- Malformed provider responses.
- Accidental leakage of API keys.

## Controls
- Strict output parsing and validation.
- Separation of config and secrets.
- Redaction of credentials in logs.

## Data Handling
- No disk persistence by default.
- Users opt-in to audit logs via stderr.

## Safety Limits
- Limit max tokens per model.
- Limit total rounds.
- Enforce timeouts per call.

## False Consensus Risk
- Multiple models can agree on incorrect or outdated information.
- For high-stakes decisions, users should independently verify outputs.

---

# Testing Strategy

## Goals
- Validate consensus loop control flow.
- Ensure deterministic aggregation and ordering.
- Verify CLI argument parsing and config merging.

## Unit Tests
- Consensus criteria logic.
- Digest construction and sorting.
- Change threshold calculation.

## Integration Tests
- Happy-path consensus loop using mocked providers.
- Quorum failure scenario.
- Parse error and recovery behavior.

## Minimal Happy-Path Test (Required)
- Setup: 3 mock participants + 1 mediator.
- Round 1: participants answer.
- Round 2: participants approve.
- Expect: consensus reached and output matches mediator candidate.

## Test Data
- Use fixed fixtures for model outputs.
- Avoid external network calls.

## Command
- pytest

---

# Roadmap

## Phase 0: Docs and Spec
- Finalize protocol and stop conditions.
- Define data models and prompt contracts.

## Phase 1: Core CLI
- Implement config loading.
- Implement provider interface and a mock provider.
- Implement consensus loop and mediator logic.
- Add pyproject.toml with runtime and dev dependencies.
- Define dependency pinning policy (major versions only).

## Phase 2: Provider Adapters
- Add OpenAI adapter.
- Add Anthropic adapter.
- Add Gemini adapter.

## Phase 3: Robustness
- Improve parse recovery.
- Add failure handling and retry policy.
- Add structured verbose audit logs.

## Phase 4: UX Polish
- Add help text and examples.
- Improve error messages.
- Add short disagreement summaries on failure.
