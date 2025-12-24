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
