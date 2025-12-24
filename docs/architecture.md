# Architecture

## Components
- CLI Frontend: parses args, loads config, triggers consensus loop.
- Orchestrator: coordinates rounds, model calls, and mediator steps.
- Provider Adapters: per-model API wrappers with a common interface.
- Consensus Engine: implements aggregation, critique processing, and stop logic.
- Audit Logger: optional verbose trace of inputs/outputs.

## Data Flow
1) CLI reads config, merges with CLI overrides.
2) Orchestrator initializes participant list and mediator.
3) Round 1: participants answer independently.
4) Mediator builds candidate answer and digest.
5) Rounds 2+: participants critique candidate; mediator updates.
6) Consensus engine checks stop criteria.
7) Output final candidate and disagreement summary.

## Module Responsibilities (Proposed)
- src/aicx/__main__.py
  - CLI entrypoint, argument parsing, exit codes.
- src/aicx/config.py
  - Load/merge configuration, validation.
- src/aicx/models/
  - Provider adapters and registry.
- src/aicx/consensus/
  - Consensus loop, digest creation, stop logic.
- src/aicx/prompts/
  - Prompt templates and rendering.
- src/aicx/logging.py
  - Verbose audit output and redaction.
- src/aicx/types.py
  - Dataclasses and shared schemas.

## Determinism
- Stable sorting of participants by name and version.
- Stable ordering of critiques and digest items.
- If randomization is added later, seed must be explicit.

## Extensibility
- Providers are pluggable via a registry.
- Prompt templates are versioned and referenced by name.
- Consensus criteria can be swapped via configuration.

## Boundary Decisions
- No caching in v1.
- No parallelization required in v1 (optionally can be added later).
- No tool-use or function-calling in v1.
