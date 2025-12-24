# Documentation Process

This document describes the collaborative process used to develop the AI Consensus CLI specification, involving two AI agents (Claude and GPT) working together with human oversight.

## Overview

The documentation was developed through an iterative feedback loop between Claude and GPT, with the human user facilitating and making final decisions. The goal was to create a comprehensive, internally consistent specification that both agents agreed upon.

## Phases

### Phase 1: Initial Spec Draft

GPT created the initial `spec.md` with the core protocol concept:
- Multi-model consensus through structured critique rounds
- Mediator-based synthesis
- Stop conditions and quorum rules

### Phase 2: Specification Expansion

GPT expanded the initial spec into a full documentation suite in `docs/`:
- `overview.md` - Goals, non-goals, principles
- `architecture.md` - Components and data flow
- `protocol.md` - Consensus protocol phases
- `consensus.md` - Criteria and stop conditions
- `data-models.md` - Dataclass schemas
- `prompts.md` - Prompt templates
- `cli.md` - CLI interface and flags
- `configuration.md` - Config file format
- `providers.md` - Provider adapter contract
- `errors.md` - Error handling
- `logging.md` - Audit trail format
- `security.md` - Security considerations
- `testing.md` - Test strategy
- `roadmap.md` - Implementation phases

### Phase 3: Claude Review

Claude reviewed all documentation and raised detailed feedback:

**Questions addressed:**
1. Mediator participating as a model (conflict of interest)
2. Model identifier inconsistencies across docs
3. Change threshold tokenization ambiguity
4. Zero successful response handling
5. JSON output reliability and parsing

**Comments:**
1. Good determinism defaults (temperature 0.2)
2. Quorum definition redundancy
3. Critical flag underspecified

**Concerns:**
1. Structured output support varies by provider
2. Token/context growth across rounds
3. Cost and latency not documented
4. False consensus risk
5. Dependency management missing
6. Duplication between AGENTS.md and docs/

### Phase 4: GPT Response

GPT addressed each item:
- Excluded mediator from participants in v1
- Created hybrid naming with alias table
- Specified whitespace tokenization
- Clarified exit codes for zero vs partial responses
- Added multi-stage JSON parsing with recovery
- Simplified quorum to `ceil(2/3 * n)`
- Added critical flag criteria to prompts
- Added `max_context_tokens` config option
- Documented cost/latency estimates
- Added false consensus warning to security.md
- Added pyproject.toml to roadmap

### Phase 5: Multi-Agent Workflow Establishment

Established formal collaboration structure:

**Directory conventions:**
- `docs/` - Shared documentation (source of truth)
- `feedback/` - Agent feedback files
- `claude/` - Claude-specific files (GPT cannot access)
- `gpt/` - GPT-specific files (Claude cannot access)

**Feedback protocol (`docs/feedback-process.md`):**
1. Each agent maintains their own feedback file
2. When reviewing, read the other agent's feedback first
3. Address their items, update shared docs as needed
4. Remove resolved items to keep files clean
5. Separate latest feedback from previous feedback

**Agent-specific configs:**
- `CLAUDE.md` - Claude's project instructions
- `gpt/init.md` - GPT's project instructions

### Phase 6: Roadmap Refinement

Claude reviewed the parallel workstream roadmap and suggested:
1. Move pyproject.toml to Phase 0
2. Add types.py to Phase 0
3. Clarify test scope in Phase 5
4. Add dependency notes between phases

GPT incorporated all suggestions:
- Added `types.py` and `pyproject.toml` to Phase 0
- Added dependency note to Phase 1 header
- Renamed Phase 5 to "Integration Testing + Packaging"

### Phase 7: Final Agreement

Both agents confirmed no blocking concerns. The specification is ready for implementation.

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| Mediator not a participant | Avoids bias and conflict of interest |
| Whitespace tokenization | Simple, deterministic, no dependencies |
| Multi-stage JSON parsing | Handles real-world model output variations |
| Exit code 2 vs 3 | Distinguishes zero responses from partial quorum failure |
| Phase 0 foundations | types.py and pyproject.toml needed before parallel work |
| Separate feedback files | Clear ownership, avoids edit conflicts |
| Latest/Previous sections | Easy to see what's new in each review cycle |

## Lessons Learned

1. **Explicit directory rules prevent conflicts** - Clear ownership of files/directories avoids agents stepping on each other.

2. **Feedback protocol needs structure** - Without clear workflow, agents may talk past each other. The "read other's feedback first" rule ensures responses are addressed.

3. **Remove resolved items** - Feedback files become cluttered quickly. Regular cleanup keeps focus on active issues.

4. **Separate latest from previous** - Makes it easy to see what's new in each review cycle.

5. **Human facilitation is key** - The user resolved ambiguities, made tie-breaking decisions, and kept the process moving forward.

## Files Created

```
docs/
  overview.md, architecture.md, protocol.md, consensus.md,
  data-models.md, prompts.md, cli.md, configuration.md,
  providers.md, errors.md, logging.md, runtime.md,
  security.md, testing.md, roadmap.md, feedback-process.md,
  glossary.md, README.md

feedback/
  FEEDBACK_CLAUDE.md, FEEDBACK_GPT.md

claude/
  skills.md

.claude/
  commands/feedback.md, commands/spec.md

gpt/
  init.md, notes.md

AGENTS.md, CLAUDE.md, README.md, spec.md
```

## Outcome

A comprehensive, agreed-upon specification ready for parallel implementation across 5 workstreams with clear Phase 0 foundations.
