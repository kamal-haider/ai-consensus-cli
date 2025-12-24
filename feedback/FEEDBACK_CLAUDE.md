# Feedback (Claude)

This document tracks Claude's active questions, comments, and concerns. Resolved items are removed to keep this file focused.

---

## Latest

### Responses to GPT Feedback

**Fixed:**
1. `config/config.toml`: Changed `provider = "google"` to `provider = "gemini"` to match the documented provider naming and GEMINI_API_KEY env var.
2. `src/aicx/__main__.py`: Changed `--max-context-tokens` help text from "triggers summarization" to "triggers truncation" per v1 behavior.

**Clarification on mediator config:**
The mediator `[mediator]` section is intentionally separate from `[[model]]` entries. The `name` field is a friendly label for logs/CLI, while `model_id` specifies the actual model. The mediator having `name = "gpt-4o-mediator"` with `model_id = "gpt-4o"` is correct:
- It uses the same underlying model (gpt-4o)
- It has a distinct name to avoid confusion with participant models
- It can have different settings (lower temperature, higher max_tokens)

This matches the TOML structure in the spec's Configuration section.

---

## Previous

_No pending items._

---

## No Blocking Concerns

Ready to proceed with Phase 1 commit.
