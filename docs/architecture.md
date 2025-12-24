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

## Module Responsibilities (Implemented)

```
src/aicx/
├── __main__.py          # CLI entrypoint, argparse, exit codes
├── config.py            # TOML loading, validation, CLI override merging
├── logging.py           # JSONL audit logging, secret redaction
├── types.py             # Frozen dataclasses: ModelConfig, RunConfig, RetryConfig, etc.
├── consensus/
│   ├── __init__.py
│   ├── runner.py        # Consensus loop orchestration, budget integration
│   ├── digest.py        # Digest construction with deterministic ordering
│   ├── stop.py          # Stop conditions, Levenshtein change threshold
│   ├── errors.py        # ZeroResponseError, check_round_responses
│   └── collection.py    # Response collection with failure tracking
├── context/
│   ├── __init__.py
│   ├── tokens.py        # Token estimation (chars/4 ratio)
│   ├── budget.py        # ContextBudget tracking, would_exceed_budget
│   └── truncation.py    # Oldest-round truncation, truncated digest
├── models/
│   ├── __init__.py
│   ├── registry.py      # ProviderAdapter protocol, ProviderRegistry, alias table
│   ├── errors.py        # Error mapping utilities (network, API, parse)
│   ├── mock.py          # MockProvider for testing
│   ├── openai.py        # OpenAI adapter with JSON mode
│   ├── anthropic.py     # Anthropic adapter (prompt-based JSON)
│   └── gemini.py        # Gemini adapter with JSON mode
├── prompts/
│   ├── __init__.py
│   ├── templates.py     # Prompt templates for participants/mediator
│   └── parsing.py       # JSON parsing with 3-tier recovery
└── retry/
    ├── __init__.py
    ├── classifier.py    # RETRYABLE_CODES, is_retryable
    ├── executor.py      # Exponential backoff, execute_with_retry
    └── wrapper.py       # RetryableProvider, wrap_with_retry

config/
└── config.toml          # Default configuration

tests/
├── __init__.py
├── test_config.py       # Config loading tests
├── test_runner.py       # Consensus loop tests
├── test_digest.py       # Digest construction tests
├── test_stop.py         # Stop condition tests
├── test_quorum.py       # Quorum handling and zero-response tests
├── test_context.py      # Context budget and truncation tests
├── test_retry.py        # Retry policy and backoff tests
├── test_mock.py         # Mock provider tests
├── test_openai.py       # OpenAI adapter tests
├── test_anthropic.py    # Anthropic adapter tests
├── test_gemini.py       # Gemini adapter tests
├── test_parsing.py      # JSON parsing tests
└── test_logging.py      # Logging tests
```

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
