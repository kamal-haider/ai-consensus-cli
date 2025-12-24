# Roadmap

This roadmap is organized for parallel workstreams with minimal overlap. Each task should be modular and mergeable independently.

## Phase 0: Shared Foundations ✅ COMPLETE
- [x] Lock protocol and stop criteria decisions in docs.
- [x] Finalize data models and prompt contracts.
- [x] Add `src/aicx/types.py` dataclasses used across workstreams.
- [x] Agree on provider alias table and JSON parsing strategy.
- [x] Add `pyproject.toml` with dependencies and pinning policy.

## Phase 1: Modular Workstreams (Parallel) ✅ COMPLETE
Dependencies: Phase 1B and 1D expect Phase 0 data models; Phase 2 depends on Phase 1C.

### A) Configuration + CLI Wiring ✅
- [x] Implement TOML config loading and validation (`src/aicx/config.py`)
- [x] Add CLI flag parsing with overrides (`src/aicx/__main__.py`)
- [x] Add config schema tests (`tests/test_config.py` - 13KB)

### B) Consensus Engine Core ✅
- [x] Implement deterministic consensus loop scaffolding (`src/aicx/consensus/runner.py`)
- [x] Implement digest construction and ordering rules (`src/aicx/consensus/digest.py`)
- [x] Implement stop conditions and change-threshold logic (`src/aicx/consensus/stop.py`)
- [x] Tests: `tests/test_runner.py`, `tests/test_digest.py`, `tests/test_stop.py`

### C) Provider Interface + Mock ✅
- [x] Implement provider registry and adapter interface (`src/aicx/models/registry.py`)
- [x] Add a mock provider for tests (`src/aicx/models/mock.py`)
- [x] Define provider error mapping (`src/aicx/models/errors.py`)
- [x] Tests: `tests/test_mock.py` (82 tests)

### D) Prompt Rendering + Parsing ✅
- [x] Implement prompt rendering helpers (`src/aicx/prompts/templates.py`)
- [x] Implement JSON parsing with recovery and strict mode (`src/aicx/prompts/parsing.py`)
- [x] Add parsing tests and fixtures (`tests/test_parsing.py`)

### E) Logging + Audit Trail ✅
- [x] Implement verbose JSONL logging with events (`src/aicx/logging.py`)
- [x] Add redaction rules for secrets
- [x] Add logging tests for event shapes (`tests/test_logging.py`)

## Phase 2: Provider Adapters (Parallel) ✅ COMPLETE
- [x] OpenAI adapter with JSON mode support (`src/aicx/models/openai.py`)
  - Uses `response_format={"type": "json_object"}`
  - Tests: `tests/test_openai.py`
- [x] Anthropic adapter with prompt-based JSON compliance (`src/aicx/models/anthropic.py`)
  - Uses `system` as separate parameter per Anthropic API
  - Tests: `tests/test_anthropic.py`
- [x] Gemini adapter with JSON mode support (`src/aicx/models/gemini.py`)
  - Uses `response_mime_type="application/json"`
  - Tests: `tests/test_gemini.py`

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
