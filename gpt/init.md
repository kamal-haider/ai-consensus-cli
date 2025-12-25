# GPT Init

This file captures GPT-specific operating rules. Update it whenever the user changes protocol or rule instructions.

## Current Rules
- Treat `docs/` and `gpt/` rule files as the source of truth.
- Follow `docs/feedback-process.md` when asked to check/review/address feedback.
- Track GPT feedback in `feedback/FEEDBACK_GPT.md`.
- Do not read or update any Claude-related files or directories.
- If any file in `docs/` changes, record it in `feedback/FEEDBACK_GPT.md`.
- Keep the latest feedback separated from previous feedback in `feedback/FEEDBACK_GPT.md`.
- Do not create mirror copies of `docs/` in `gpt/`; reference `docs/` directly.
