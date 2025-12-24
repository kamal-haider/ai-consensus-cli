# CLAUDE.md

## Project Overview

AI Consensus CLI (`aicx`) - A command-line tool that sends prompts to multiple AI models, runs structured critique rounds, and returns a consensus response.

**Status:** Early ideation phase. No code written yet.

## Source of Truth

**Primary reference:** `claude/skills.md` - Complete specification with all docs combined. Always consult this file for implementation details.

## Feedback Protocol

When the user says "check for feedback" or similar, follow `docs/feedback-process.md`.

**Rules:**
- When making any changes to files in `docs/`, record those changes in `feedback/FEEDBACK_CLAUDE.md`
- Keep `feedback/FEEDBACK_CLAUDE.md` clean: remove resolved items when context changes
- Only keep active questions, comments, and concerns in the feedback file
- Separate latest feedback from previous feedback using `## Latest` and `## Previous` sections

## Directory Rules

| Directory | Rule |
|-----------|------|
| `claude/` | Claude-specific files (skills, reference docs) |
| `gpt/` | **NEVER read or modify** - GPT-specific files |
| `feedback/` | Feedback files for both agents |
| `docs/` | Shared documentation (record changes in feedback file) |
| `.claude/` | Claude Code configuration and slash commands |
| `AGENTS.md` | **NEVER modify** - Shared agent guidelines (read-only) |

## Slash Commands

- `/spec` - Review the full specification from `claude/skills.md`
- `/feedback` - Check and respond to GPT feedback

## Key Documentation

- `claude/skills.md` - **Primary reference** (all specs combined)
- `spec.md` - Initial protocol draft and open questions
- `docs/` - Individual specification files:
  - `overview.md` - Goals, non-goals, principles
  - `architecture.md` - Components and data flow
  - `protocol.md` - Consensus protocol phases
  - `consensus.md` - Criteria and stop conditions
  - `data-models.md` - Dataclass schemas
  - `prompts.md` - Prompt templates
  - `cli.md` - CLI interface and flags
  - `configuration.md` - Config file format (TOML)
  - `providers.md` - Provider adapter contract
  - `errors.md` - Error handling and exit codes
  - `logging.md` - Verbose/audit logging format
  - `security.md` - Security considerations
  - `testing.md` - Test conventions
  - `roadmap.md` - Phased milestones

## Project Structure (Planned)

```
claude/
  skills.md      # Complete specification (source of truth)
.claude/
  commands/      # Slash commands (/spec, /feedback)
feedback/
  FEEDBACK_CLAUDE.md  # Claude's feedback/questions
  FEEDBACK_GPT.md     # GPT's feedback/questions
docs/
  feedback-process.md # Shared feedback protocol
  *.md                # Individual spec documents
src/aicx/
  __main__.py    # CLI entrypoint
  config.py      # Config loading/validation
  types.py       # Dataclasses and schemas
  logging.py     # Verbose audit output
  consensus/     # Consensus loop, digest, stop logic
  models/        # Provider adapters
  prompts/       # Prompt templates
config/
  config.toml    # Default configuration
tests/
  test_*.py      # Pytest tests
```

## Commands

```bash
# Run CLI (planned)
aicx "your prompt"
aicx "prompt" --models gpt-4o,claude-3-5 --rounds 2 --verbose

# Run tests
pytest

# Install for development (once pyproject.toml exists)
pip install -e .
```

## Coding Conventions

- **Language:** Python 3.11+
- **Data structures:** Use dataclasses for structured data between stages
- **Determinism:** Stable sorting, explicit seeds for any randomization
- **Output:** Clean by default; verbose/audit only with `--verbose`
- **Logging:** Write to stderr as JSON lines in verbose mode only
- **ASCII:** Avoid non-ASCII unless file already uses it

## Architecture Principles

- Fail fast on config errors
- Continue on individual model failures if quorum is met
- Mediator failure aborts the run
- No disk writes by default
- No caching in v1
- Sequential execution in v1 (parallel optional later)

## Provider Environment Variables

```
OPENAI_API_KEY
ANTHROPIC_API_KEY
GEMINI_API_KEY
```

## Consensus Protocol Summary

1. Round 1: All participants answer independently
2. Mediator synthesizes candidate answer + digest
3. Round 2+: Participants critique candidate
4. Mediator updates based on critiques
5. Stop when: consensus reached OR max rounds (3) OR change < 10%

**Consensus criteria:** >= 2/3 approvals AND zero critical objections

**Note:** The mediator is not a participant in v1. It synthesizes and updates but does not contribute answers or votes.

## Exit Codes

- 0: Success
- 1: Configuration error
- 2: Provider/network error (including zero successful responses)
- 3: Quorum failure (some responses, but below threshold)
- 4: Internal error
