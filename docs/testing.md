# Testing Strategy

## Goals
- Validate provider adapters work correctly
- Verify CLI argument parsing
- Ensure error handling is robust

## Test Structure

```
tests/
  test_providers.py   # Provider adapter tests (mocked)
  test_cli.py         # CLI argument parsing
  test_config.py      # Configuration loading
```

## Commands

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_providers.py -v

# Run with coverage
pytest --cov=src/aicx
```

## Test Data
- Use mocked API responses
- No external network calls in tests
- All provider tests use `unittest.mock`

## Minimal Happy-Path Test

```python
def test_query_returns_response():
    """Query a model and get a response."""
    with mock_openai_response("Hello, world!"):
        result = query("Say hello", model="gpt-4o")
        assert result == "Hello, world!"
```
