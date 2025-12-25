# Feedback (Claude)

This document tracks Claude's active questions, comments, and concerns. Resolved items are removed to keep this file focused.

---

## Latest

### Provider Wiring Complete - Real Providers Connected to Runner

**Implemented:**

1. **Provider Factory (`src/aicx/models/factory.py`)**:
   - `create_provider(ModelConfig)` - Instantiates OpenAI, Anthropic, Gemini, or Mock providers
   - `create_providers(configs)` - Creates providers for multiple models
   - `get_available_providers()` - Lists registered providers
   - Automatic retry wrapping when ModelConfig has retry config

2. **Runner Updates (`src/aicx/consensus/runner.py`)**:
   - Added helper functions: `_format_digest()`, `_format_responses_for_mediator()`, `_format_critiques_for_mediator()`
   - Replaced all 4 stub functions with real implementations:
     - `_collect_round1_responses()` - Calls participants with `participant_prompt()`
     - `_synthesize_candidate()` - Calls mediator with `mediator_synthesis_prompt()`
     - `_collect_critique_responses()` - Calls participants with `critique_prompt()`
     - `_update_candidate()` - Calls mediator with `mediator_update_prompt()`
   - Providers created once at start and reused throughout consensus loop

3. **Test Fixture Updates (`tests/test_runner.py`)**:
   - Changed fixtures from real provider names to `mock` provider
   - Ensures unit tests work without API keys

**All 418 tests pass.**

**CLI is now fully functional:**
- With API keys set: Uses real OpenAI, Anthropic, Gemini providers
- Without API keys: Tests use mock providers

---

## Previous

### Phase 5 Complete - Integration Testing + Packaging

Integration tests (27 tests), Python 3.10+ support, tomli dependency.

### Phase 4 Complete - UX + Docs Polish

CLI help, error docs, disagreement summary with confidence indicator.

### Phase 3 Complete - Robustness + Limits

Quorum handling, context budget, retry policy.

### Phase 2 Complete - Provider Adapters

### Phase 1 Complete - Core Implementation

---

## Project Status

All 5 phases + provider wiring implemented:
- Phase 0: Foundations
- Phase 1: Core Implementation
- Phase 2: Provider Adapters
- Phase 3: Robustness + Limits
- Phase 4: UX + Docs Polish
- Phase 5: Integration Testing + Packaging
- Post-Phase: Provider wiring (stubs replaced with real calls)

**Uncommitted changes:**
- `src/aicx/models/factory.py` (new)
- `src/aicx/models/__init__.py` (factory exports)
- `src/aicx/consensus/runner.py` (real provider calls)
- `tests/test_runner.py` (mock provider fixtures)

Ready for commit and real-world testing with API keys.
