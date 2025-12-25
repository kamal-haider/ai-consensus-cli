# AGENTS

## Project Summary
- Goal: CLI that orchestrates multiple AI models to converge on a consensus response.
- Language: Python
- Status: early ideation; see `spec.md`.

## Working Agreement
- Keep changes small and reviewable.
- Prefer clear, explicit code over clever abstractions.
- Avoid introducing non-ASCII unless the file already uses it.

## Repo Conventions
- Place Python sources under `src/`.
- Keep config/templates in `config/`.
- Add tests under `tests/` and name them `test_*.py`.
- Keep CLI entrypoint in `src/aicx/__main__.py`.

## Coding Guidelines
- Prefer dataclasses for structured data passed between stages.
- Make the consensus loop deterministic by default.
- Log only in verbose mode; default output should be clean.

## Tooling
- Use `rg` for searching.
- If adding dependencies, document them in the README.

## Testing
- If tests are added, include a minimal happy-path test for the consensus loop.

## Feedback Protocol
- Always treat `docs/` and `gpt/` rules as the source of truth.
- If the user says \"check for feedback\" (or similar), follow `docs/feedback-process.md`.
- GPT feedback is tracked in `feedback/FEEDBACK_GPT.md`.
- Do not read or update any docs in the Claude directory.
- Do not edit `CLAUDE.md`.
- Do not touch any Claude-related files or directories.
- If protocol or operating rules change, update the `/init` file accordingly.
- In `feedback/FEEDBACK_GPT.md`, keep the latest update separated from previous updates.
- Do not create mirror copies of `docs/` in `gpt/`; reference `docs/` directly.
