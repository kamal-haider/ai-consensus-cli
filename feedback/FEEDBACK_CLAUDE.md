# Feedback (Claude)

This document tracks Claude's active questions, comments, and concerns. Resolved items are removed to keep this file focused.

---

## Latest

### Phase 6A-D Complete - Setup Wizard & Configuration UX

Implemented and tested:

**A) Interactive Setup Guide (`--setup`)** ✅
- Interactive wizard to configure default models and mediator
- Saves to user config (`~/.config/aicx/config.toml`)
- Validates API keys for selected providers
- Shows available models per provider

**B) Default Model Behavior** ✅
- `aicx "prompt"` without `--models` uses configured defaults
- Fallback chain: CLI flags → user config → project config → built-in defaults
- Ad-hoc model resolution from model ID prefixes (gpt-*, claude-*, gemini-*)

**C) Model Shorthand Aliases** ✅
- `--models gpt claude gemini` expands to full model names
- Maps to user's configured default version for each provider
- Allows mixing shorthand and full names

**D) Status Command (`--status`)** ✅
- Shows default models, mediator, API key status
- Lists config file locations and available aliases

### Remaining Phase 6 Work

**E) Interactive Help Assistant (`--help "question"`)**
- AI-powered help for CLI questions
- Uses mediator model, scoped to CLI topics only
- Can suggest or run commands

**F) Digest Improvements for Structured Data**
- Detect JSON responses and skip sentence-based digest
- Reduces false "digest format" objections from models

---

## Previous

### v1.0 Released

Tagged and released on GitHub with full consensus protocol, all 3 providers, and 438 tests.

### Phase 6 Planned - Configuration UX + Interactive Help

### Phase 5 Complete - Integration Testing + Packaging

### Phase 4 Complete - UX + Docs Polish

### Phase 3 Complete - Robustness + Limits

### Phase 2 Complete - Provider Adapters

### Phase 1 Complete - Core Implementation

---

## Project Status

**Completed:** Phases 0-5 + v1.0 release + Phase 6A-D (setup wizard)
**In Progress:** Phase 6E-F (interactive help, digest improvements)

**New files:**
- `src/aicx/user_config.py` - User config management
- `src/aicx/setup.py` - Interactive setup wizard
- `tests/test_user_config.py` - User config tests (20 tests)

**Modified files:**
- `src/aicx/__main__.py` - Added --setup, --status flags
- `src/aicx/config.py` - Added user prefs and shorthand expansion
- `docs/roadmap.md` - Phase 6A-D marked complete

**All 438 tests pass.**
