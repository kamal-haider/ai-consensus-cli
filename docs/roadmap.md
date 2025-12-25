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

## Phase 3: Robustness + Limits ✅ COMPLETE

### A) Quorum & Zero-Response Handling ✅
- [x] ZeroResponseError for all-models-failed scenario (`src/aicx/consensus/errors.py`)
- [x] `check_round_responses()` helper for quorum validation
- [x] `collect_responses_with_failures()` with failure tracking (`src/aicx/consensus/collection.py`)
- [x] FailedModel dataclass for error tracking
- [x] Per-round quorum checks in runner (Round 1 + critique rounds)
- [x] Failed models tracked in ConsensusResult metadata
- [x] Tests: `tests/test_quorum.py`

### B) Context Budget Enforcement ✅
- [x] Token estimation using chars/4 ratio (`src/aicx/context/tokens.py`)
- [x] ContextBudget dataclass with immutable tracking (`src/aicx/context/budget.py`)
- [x] `track_usage()` and `would_exceed_budget()` helpers
- [x] `truncate_oldest_rounds()` - removes oldest rounds first (`src/aicx/context/truncation.py`)
- [x] `build_truncated_digest()` for truncated response digests
- [x] Runner integration with budget initialization, tracking, and truncation events
- [x] Tests: `tests/test_context.py`

### C) Retry Policy ✅
- [x] RetryConfig dataclass with validation (`src/aicx/types.py`)
- [x] `retry` field added to ModelConfig
- [x] Error classification: RETRYABLE_CODES vs NON_RETRYABLE_CODES (`src/aicx/retry/classifier.py`)
- [x] `calculate_delay()` with exponential backoff and jitter (`src/aicx/retry/executor.py`)
- [x] `execute_with_retry()` for retry execution logic
- [x] RetryableProvider wrapper for transparent retry (`src/aicx/retry/wrapper.py`)
- [x] `wrap_with_retry()` utility function
- [x] Tests: `tests/test_retry.py`

## Phase 4: UX + Docs Polish ✅ COMPLETE

### A) CLI Help Text ✅
- [x] Added epilog with usage examples and exit codes
- [x] Grouped arguments by category (Model Selection, Consensus, Context, Behavior, Config)
- [x] Added `--version` flag
- [x] Improved help descriptions with metavars

### B) Error Messages ✅
- [x] Updated `docs/errors.md` with comprehensive error type documentation
- [x] Added resolution steps for each error type
- [x] Documented retry configuration (now implemented)
- [x] Added exit code reference table

### C) Disagreement Summary + Confidence ✅
- [x] Added `_calculate_confidence()` function (HIGH/MEDIUM/LOW based on approvals and critical objections)
- [x] Enhanced `_build_disagreement_summary()` with:
  - Consensus status line with approval count
  - Confidence indicator
  - Categorized issues (Critical/Objection/Missing)
- [x] Updated `docs/cli.md` with output format documentation

## Phase 5: Integration Testing + Packaging ✅ COMPLETE

### A) Integration Tests ✅
- [x] Created `tests/test_integration.py` with 27 tests covering:
  - Full consensus loop happy path (5 tests)
  - Consensus with various options (3 tests)
  - CLI parser argument handling (9 tests)
  - CLI version verification (1 test)
  - Config loading integration (4 tests)
  - Mock provider integration (3 tests)
  - End-to-end CLI tests via subprocess (2 tests)

### B) Packaging Setup ✅
- [x] Updated `pyproject.toml`:
  - Python 3.10+ support (was 3.11+)
  - Added `tomli` conditional dependency for Python 3.10
  - Updated classifiers to "Alpha" status
  - Added Python 3.10 classifier

**Test count: 418 tests (391 unit + 27 integration)**

## Phase 6: Configuration UX + Interactive Help (In Progress)

### A) Interactive Setup Guide ✅
- [x] `--setup` flag launches interactive configuration wizard
- [x] Prompt user to select default models (from available providers)
- [x] Prompt user to select default mediator
- [x] Save preferences to user config (`~/.config/aicx/config.toml`)
- [x] Validate API keys are set for selected providers
- [x] Show confirmation of saved settings

### B) Default Model Behavior ✅
- [x] Running `aicx "prompt"` without `--models` uses configured defaults
- [x] Defaults stored in user config, separate from project config
- [x] Fallback chain: CLI flags → user config → project config → built-in defaults

### C) Model Shorthand Aliases ✅
- [x] Support shorthand names: `gpt`, `claude`, `gemini`
- [x] Map to user's configured default version for each provider
- [x] Example: `--models gpt claude` expands to `gpt-4o,claude-sonnet-4` (or user's defaults)
- [x] Allow mixing shorthand and full names: `--models gpt claude-sonnet-4-20250514`

### D) Status Command ✅
- [x] `--status` shows current configuration summary:
  - Default models configured
  - Default mediator
  - API key status (set/not set, not the actual keys)
  - Config file locations being used
  - Available model aliases

### E) Interactive Help Assistant
- [ ] `--help "question"` invokes AI assistant for CLI questions
- [ ] Uses mediator model to answer questions about CLI usage
- [ ] Scoped to CLI-related questions only (not general knowledge)
- [ ] Can suggest commands or offer to run them
- [ ] Example: `--help "How do I configure a new model?"` → explains or runs `--setup`
- [ ] Distinguishes from `--help` (no argument) which shows traditional help menu
- [ ] Response should be concise and actionable

### F) Digest Improvements for Structured Data
- [ ] Detect JSON/structured data in responses
- [ ] Skip sentence-based digest for structured data
- [ ] Generate prose summary for JSON responses (optional)
- [ ] Reduce false "digest format" objections from models

## Phase 7: Future Enhancements (Ideas)
- [ ] Parallel model calls (concurrent API requests)
- [ ] Streaming output support
- [ ] Local model support (Ollama, llama.cpp)
- [ ] Web UI for consensus visualization
- [ ] Plugin system for custom providers
