# Feedback Process (Source of Truth)

This document defines the shared feedback protocol between GPT and Claude agents. All agents must follow it when the user references feedback (e.g., "check for feedback").

## Trigger Phrases
When the user says something like:
- "check for feedback"
- "review the feedback"
- "address feedback"

follow this protocol.

## Files and Responsibilities
- Shared docs live in `docs/` and are the source of truth for specification.
- Feedback files live in `feedback/` directory.
- GPT-only rules live in `gpt/`. Claude must not read or update any files in `gpt/`.
- Claude-specific files live in `claude/`. GPT must not read or update any files in `claude/`.


## Standard Workflow
1) Keep your questions/comments/concerns in **your own** feedback file (this is where you originate items):
   - GPT uses `feedback/FEEDBACK_GPT.md`
   - Claude uses `feedback/FEEDBACK_CLAUDE.md`
   - Remove items that are resolved, once context evolves.
   - Add any new questions or concerns.
   - Record any changes made to files in `docs/`.
   - Keep the latest feedback separated from previous feedback.
2) When it's time to review feedback, **start by reading your own feedback file** and look for the other agent's answers to your items.
3) Then read the other agent's feedback file and address any questions/comments/concerns they created after reviewing your follow-up:
   - Claude addresses items in `feedback/FEEDBACK_GPT.md`
   - GPT addresses items in `feedback/FEEDBACK_CLAUDE.md`
4) Update shared docs in `docs/` as needed to reflect decisions.
5) Summarize changes and note any remaining open items.

## Rules
- If the user updates operating protocol or rules, update your agent's config file accordingly.
- Only shared documents belong in `docs/`.
- Any GPT-only rules should live under `gpt/`.
- Any Claude-only rules should live under `claude/`.
- If any file in `docs/` is changed, it must be noted in your agent feedback file.
