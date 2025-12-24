# Feedback (Claude)

This document tracks Claude's active questions, comments, and concerns. Resolved items are removed to keep this file focused.

---

## Latest

### Phase 3 Complete - Robustness + Limits Implemented

**Completed using parallel worktrees:**

1. **Phase 3A: Quorum & Zero-Response Handling**
   - `src/aicx/consensus/errors.py` - ZeroResponseError, check_round_responses helper
   - `src/aicx/consensus/collection.py` - FailedModel dataclass, collect_responses_with_failures
   - Updated `runner.py` - Per-round quorum checks, failed models in metadata
   - Tests: `tests/test_quorum.py`

2. **Phase 3B: Context Budget Enforcement**
   - `src/aicx/context/tokens.py` - Token estimation using chars/4 ratio
   - `src/aicx/context/budget.py` - ContextBudget dataclass, track_usage, would_exceed_budget
   - `src/aicx/context/truncation.py` - truncate_oldest_rounds (keeps most recent), build_truncated_digest
   - Updated `runner.py` - Budget initialization, tracking, truncation events
   - Tests: `tests/test_context.py`

3. **Phase 3C: Retry Policy**
   - `src/aicx/types.py` - Added RetryConfig dataclass, retry field to ModelConfig
   - `src/aicx/retry/classifier.py` - RETRYABLE_CODES (timeout, network, rate_limit, service_unavailable)
   - `src/aicx/retry/executor.py` - calculate_delay with exponential backoff + jitter
   - `src/aicx/retry/wrapper.py` - RetryableProvider transparent wrapper
   - Tests: `tests/test_retry.py` (40 tests)

**Documentation Updated:**
- `docs/roadmap.md` - Marked Phase 3A, 3B, 3C as complete with file references
- `docs/architecture.md` - Added consensus/errors.py, consensus/collection.py, context/, retry/ modules
- `docs/testing.md` - Added test_quorum.py, test_context.py, test_retry.py; updated coverage table

**Key Design Decisions:**
- ZeroResponseError is distinct from QuorumError (different exit codes: 2 vs 3)
- Token estimation uses chars/4 ratio (no external tokenizer in v1)
- Context truncation always preserves the most recent round
- Retry jitter uses 0-25% of base delay to avoid thundering herd
- RetryableProvider is a transparent wrapper maintaining ProviderAdapter protocol

---

## Previous

### Phase 2 Complete - Provider Adapters Implemented

**Completed:**
1. `src/aicx/models/openai.py` - OpenAI provider adapter
   - Uses `response_format={"type": "json_object"}` for native JSON mode
   - Handles APITimeoutError, APIConnectionError, RateLimitError
   - Tests: `tests/test_openai.py`

2. `src/aicx/models/anthropic.py` - Anthropic provider adapter
   - Uses `system` as separate parameter (not in messages array)
   - `supports_json=False` - relies on prompt-based JSON compliance
   - Tests: `tests/test_anthropic.py`

3. `src/aicx/models/gemini.py` - Gemini provider adapter
   - Uses `response_mime_type="application/json"` in GenerationConfig
   - Combines system+user prompts (Gemini API pattern)
   - Tests: `tests/test_gemini.py`

### Phase 1 Complete - Core Implementation

**Implemented:**
- Configuration loading and CLI (`config.py`, `__main__.py`)
- Consensus engine (`consensus/runner.py`, `digest.py`, `stop.py`)
- Provider interface and mock (`models/registry.py`, `mock.py`, `errors.py`)
- Prompt parsing with 3-tier recovery (`prompts/parsing.py`, `templates.py`)
- JSONL audit logging with redaction (`logging.py`)
- Comprehensive test suite (~250+ tests)

---

## No Blocking Concerns

Ready to proceed with Phase 4 (UX + Docs Polish) or Phase 5 (Integration Testing).
