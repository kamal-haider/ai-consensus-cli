# Roadmap

This roadmap is organized for parallel workstreams with minimal overlap. Each task should be modular and mergeable independently.

## Phase 0: Shared Foundations
- Lock protocol and stop criteria decisions in docs.
- Finalize data models and prompt contracts.
- Add `src/aicx/types.py` dataclasses used across workstreams.
- Agree on provider alias table and JSON parsing strategy.
- Add `pyproject.toml` with dependencies and pinning policy.

## Phase 1: Modular Workstreams (Parallel)
Dependencies: Phase 1B and 1D expect Phase 0 data models; Phase 2 depends on Phase 1C.

### A) Configuration + CLI Wiring
- Implement TOML config loading and validation.
- Add CLI flag parsing with overrides.
- Add config schema tests (no provider calls).

### B) Consensus Engine Core
- Implement deterministic consensus loop scaffolding.
- Implement digest construction and ordering rules.
- Implement stop conditions and change-threshold logic.

### C) Provider Interface + Mock
- Implement provider registry and adapter interface.
- Add a mock provider for tests.
- Define provider error mapping.

### D) Prompt Rendering + Parsing
- Implement prompt rendering helpers.
- Implement JSON parsing with recovery and strict mode.
- Add parsing tests and fixtures.

### E) Logging + Audit Trail
- Implement verbose JSONL logging with events.
- Add redaction rules for secrets.
- Add logging tests for event shapes.

## Phase 2: Provider Adapters (Parallel)
- OpenAI adapter with JSON mode support.
- Anthropic adapter with prompt-based JSON compliance.
- Gemini adapter with JSON mode support.

## Phase 3: Robustness + Limits
- Add quorum handling and zero-response errors.
- Add context budget enforcement (truncate oldest rounds).
- Add retry policy (if opted into v1).

## Phase 4: UX + Docs Polish
- Improve CLI help text and examples.
- Clarify error messages and exit code guidance.
- Add disagreement summaries and consensus confidence notes.

## Phase 5: Integration Testing + Packaging
- Add minimal happy-path consensus test.
