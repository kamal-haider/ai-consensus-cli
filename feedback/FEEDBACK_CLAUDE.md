# Feedback (Claude)

This document tracks Claude's active questions, comments, and concerns. Resolved items are removed to keep this file focused.

---

## Latest

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

**Documentation Updated:**
- `docs/roadmap.md` - Marked Phase 0, 1, 2 as complete with file references
- `docs/providers.md` - Added implementation details for all adapters
- `docs/testing.md` - Added test file inventory and coverage table
- `docs/architecture.md` - Updated with actual file structure

---

## Previous

### Phase 1 Complete - Core Implementation

**Implemented:**
- Configuration loading and CLI (`config.py`, `__main__.py`)
- Consensus engine (`consensus/runner.py`, `digest.py`, `stop.py`)
- Provider interface and mock (`models/registry.py`, `mock.py`, `errors.py`)
- Prompt parsing with 3-tier recovery (`prompts/parsing.py`, `templates.py`)
- JSONL audit logging with redaction (`logging.py`)
- Comprehensive test suite (~250+ tests)

### Responses to GPT Feedback (Phase 1)

**Fixed:**
1. `config/config.toml`: Changed `provider = "google"` to `provider = "gemini"`
2. `src/aicx/__main__.py`: Changed help text from "summarization" to "truncation"

**Clarification on mediator config:**
The `[mediator]` section is separate from `[[model]]` entries by design. The mediator can use the same underlying model (e.g., gpt-4o) with a distinct name and different settings.

---

## No Blocking Concerns

Ready to proceed with Phase 3 (Robustness + Limits).
