# Feedback and Open Questions (GPT)

## Latest Update
- Reviewed `feedback/FEEDBACK_CLAUDE.md` (Phase 3 fixes + test suite updates).
- Observed mismatches in this worktree vs Claude notes:
  - `config/config.toml` still uses `approval_ratio = 0.67` and mediator `gpt-4o-mediator`, while Claude notes mention a default mediator change and tests adjusted to 0.66.
  - No `tomli` fallback or related changes are visible here; likely in Claude's worktree only.
- Action needed: reconcile/merge Claude’s Phase 3 test-fix changes into this worktree or confirm which defaults should be authoritative before updating docs/config.

## Previous Updates
- Removed GPT mirror copies of `docs/` files; `gpt/` now contains only GPT-specific rules.
- Updated `AGENTS.md` and `gpt/init.md` to forbid doc mirroring.
- Added `gpt/rules.md` to describe GPT-only rules and direct `docs/` references.
- Reviewed `feedback/FEEDBACK_CLAUDE.md`; no doc changes required.
- Updated `docs/configuration.md` to clarify that the mediator is configured separately from participants.
- Flagged staged config/provider naming and mediator naming mismatches for review.
- Updated `docs/feedback-process.md` to require separating latest feedback from previous feedback.
- Moved GPT feedback to `feedback/FEEDBACK_GPT.md`.
- Updated `docs/feedback-process.md` to point to the new feedback location.
- Updated `docs/README.md` to reflect the new feedback path.
- Rewrote `docs/roadmap.md` to a parallel workstream roadmap.
- Updated `docs/roadmap.md` to add Phase 0 foundations, dependency notes, and renamed Phase 5 to integration testing + packaging.

## Open Questions
- Which defaults should we treat as authoritative: `approval_ratio = 0.67` (docs/config) or `0.66` (Claude test updates)?
- Should the default mediator be a separate model (e.g., gemini-1.5-pro) as Claude notes, or keep `gpt-4o-mediator` in config?

## Notes
- GPT feedback is tracked in `feedback/FEEDBACK_GPT.md`.
