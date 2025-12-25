# Feedback (Claude)

This document tracks Claude's active questions, comments, and concerns. Resolved items are removed to keep this file focused.

---

## Latest

### Phase 6 Planned - Configuration UX + Interactive Help

Added to roadmap (`docs/roadmap.md`):

**A) Interactive Setup Guide (`--setup`)**
- Interactive wizard to configure default models and mediator
- Saves to user config (`~/.config/aicx/config.toml`)
- Validates API keys for selected providers

**B) Default Model Behavior**
- `aicx "prompt"` without `--models` uses configured defaults
- Fallback chain: CLI flags → user config → project config → built-in defaults

**C) Model Shorthand Aliases**
- `--models gpt claude gemini` expands to full model names
- Maps to user's configured default version for each provider
- Allows mixing shorthand and full names

**D) Status Command (`--status`)**
- Shows default models, mediator, API key status
- Lists config file locations and available aliases

**E) Interactive Help Assistant (`--help "question"`)**
- AI-powered help for CLI questions
- Uses mediator model, scoped to CLI topics only
- Can suggest or run commands (e.g., `--help "configure new model"` → runs `--setup`)
- Distinguishes from `--help` (traditional help menu)

**F) Digest Improvements for Structured Data**
- Detect JSON responses and skip sentence-based digest
- Reduces false "digest format" objections from models

### Bug Fixes Committed

**Provider wiring + JSON fixes (`b8f3c0f` + uncommitted):**
- Anthropic prefill for reliable JSON output
- JSON extraction from markdown code blocks
- Non-string answer serialization (lists/dicts → JSON strings)
- Updated config with valid Claude model ID

---

## Previous

### Provider Wiring Complete

Factory pattern, real provider calls, retry integration.

### Phase 5 Complete - Integration Testing + Packaging

### Phase 4 Complete - UX + Docs Polish

### Phase 3 Complete - Robustness + Limits

### Phase 2 Complete - Provider Adapters

### Phase 1 Complete - Core Implementation

---

## Project Status

**Completed:** Phases 0-5 + provider wiring + JSON fixes
**Planned:** Phase 6 (Configuration UX + Interactive Help)

**Uncommitted changes:**
- `src/aicx/models/anthropic.py` (prefill + JSON extraction)
- `src/aicx/models/openai.py` (non-string answer serialization)
- `src/aicx/models/gemini.py` (non-string answer serialization)
- `src/aicx/models/registry.py` (updated model aliases)
- `tests/test_anthropic.py` (prefill test updates)
- `config/config.toml` (valid Claude model ID)
- `docs/roadmap.md` (Phase 6 added)

**All 418 tests pass.**
