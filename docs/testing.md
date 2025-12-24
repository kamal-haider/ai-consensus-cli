# Testing Strategy

## Goals
- Validate consensus loop control flow.
- Ensure deterministic aggregation and ordering.
- Verify CLI argument parsing and config merging.

## Test Files

### Configuration & CLI
- `tests/test_config.py` - TOML config loading, validation, CLI override merging

### Consensus Engine
- `tests/test_runner.py` - Consensus loop orchestration, round management
- `tests/test_digest.py` - Digest construction, deterministic ordering
- `tests/test_stop.py` - Stop conditions, Levenshtein change threshold (47 tests)

### Providers
- `tests/test_mock.py` - MockProvider and factory functions (82 tests)
- `tests/test_openai.py` - OpenAI adapter with mocked client
- `tests/test_anthropic.py` - Anthropic adapter with mocked client
- `tests/test_gemini.py` - Gemini adapter with mocked client

### Parsing & Logging
- `tests/test_parsing.py` - JSON parsing with 3-tier recovery, strict mode
- `tests/test_logging.py` - JSONL audit logging, secret redaction

## Unit Tests
- Consensus criteria logic (`test_stop.py`)
- Digest construction and sorting (`test_digest.py`)
- Change threshold calculation using Levenshtein distance (`test_stop.py`)
- Provider error mapping (`test_*.py` for each provider)

## Integration Tests
- Happy-path consensus loop using mocked providers (`test_runner.py`)
- Quorum failure scenario (`test_runner.py`)
- Parse error and recovery behavior (`test_parsing.py`)

## Minimal Happy-Path Test (Required)
- Setup: 3 mock participants + 1 mediator.
- Round 1: participants answer.
- Round 2: participants approve.
- Expect: consensus reached and output matches mediator candidate.

## Test Data
- Use fixed fixtures for model outputs.
- Avoid external network calls.
- All provider tests use `unittest.mock` to mock API clients.

## Commands
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_stop.py -v

# Run with coverage
pytest --cov=src/aicx

# Run tests matching pattern
pytest -k "test_timeout"
```

## Test Coverage Areas
| Module | Test File | Focus |
|--------|-----------|-------|
| `config.py` | `test_config.py` | TOML loading, validation, overrides |
| `consensus/runner.py` | `test_runner.py` | Loop orchestration |
| `consensus/digest.py` | `test_digest.py` | Digest construction |
| `consensus/stop.py` | `test_stop.py` | Stop conditions |
| `models/mock.py` | `test_mock.py` | Mock provider |
| `models/openai.py` | `test_openai.py` | OpenAI adapter |
| `models/anthropic.py` | `test_anthropic.py` | Anthropic adapter |
| `models/gemini.py` | `test_gemini.py` | Gemini adapter |
| `prompts/parsing.py` | `test_parsing.py` | JSON parsing |
| `logging.py` | `test_logging.py` | Audit logging |

