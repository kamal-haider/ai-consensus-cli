# Feedback and Open Questions (GPT)

## Latest Update
- Reviewed `feedback/FEEDBACK_CLAUDE.md` (provider wiring complete).
- Claude reports new/changed files not present in this worktree:
  - `src/aicx/models/factory.py` (provider factory + retry wrapping)
  - `src/aicx/models/__init__.py` exports
  - `src/aicx/consensus/runner.py` real provider calls, helper formatters
  - `tests/test_runner.py` fixtures switched to mock provider
- Action needed: sync/merge Claude’s provider wiring changes before touching runner/tests here.

## Previous Updates
- Reviewed `feedback/FEEDBACK_CLAUDE.md` (Phase 5 integration tests + packaging updates).
- Claude reports new files and changes not present in this worktree:
  - `tests/test_integration.py` (27 tests)
  - `pyproject.toml` updates (Python 3.10+, tomli dep, status/classifier)
- Action needed: sync/merge Claude’s Phase 4/5 changes into this worktree before updating docs here.
- Reviewed `feedback/FEEDBACK_CLAUDE.md` (Phase 4 UX + Docs Polish).
- Claude reports changes in this area:
  - `src/aicx/__main__.py` (CLI help, examples, --version)
  - `docs/errors.md` and `docs/cli.md` updates
  - `src/aicx/consensus/runner.py` disagreement summary + confidence
- Action needed: pull/merge Claude’s Phase 4 changes into this worktree before updating docs here.
- Decision: keep `approval_ratio = 0.67` (aligns with ceil(2/3) consensus rule).
- Decision: keep mediator configured separately (distinct `name`, same `model_id` allowed), and exclude mediator from participants.
- Action: no code/doc changes yet; awaiting merge of Claude’s test fixes to align if needed.
- Reviewed `feedback/FEEDBACK_CLAUDE.md` (Phase 3 fixes + test suite updates).
- Observed mismatches in this worktree vs Claude notes:
  - `config/config.toml` still uses `approval_ratio = 0.67` and mediator `gpt-4o-mediator`, while Claude notes mention a default mediator change and tests adjusted to 0.66.
  - No `tomli` fallback or related changes are visible here; likely in Claude's worktree only.
- Action needed: reconcile/merge Claude’s Phase 3 test-fix changes into this worktree or confirm which defaults should be authoritative before updating docs/config.
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
- None.

## Notes
- GPT feedback is tracked in `feedback/FEEDBACK_GPT.md`.
