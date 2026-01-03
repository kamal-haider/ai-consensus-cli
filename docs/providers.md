# Provider Adapters

## Supported Providers

### OpenAI
- **Models**: gpt-4o, gpt-4-turbo, gpt-3.5-turbo
- **Env var**: `OPENAI_API_KEY`
- **JSON mode**: Native support via `response_format`

### Anthropic
- **Models**: claude-3-5-sonnet, claude-3-opus, claude-3-haiku
- **Env var**: `ANTHROPIC_API_KEY`
- **JSON mode**: Prompt-based only

### Google Gemini
- **Models**: gemini-1.5-pro, gemini-1.5-flash
- **Env var**: `GEMINI_API_KEY`
- **JSON mode**: Native support via `response_mime_type`

## Model Aliases

| Alias | Provider | Model ID |
|-------|----------|----------|
| gpt-4o | OpenAI | gpt-4o |
| gpt-4-turbo | OpenAI | gpt-4-turbo |
| claude-sonnet | Anthropic | claude-3-5-sonnet-20241022 |
| claude-opus | Anthropic | claude-3-opus-20240229 |
| gemini | Google | gemini-1.5-pro |
| gemini-flash | Google | gemini-1.5-flash |

Unknown aliases are passed through verbatim to the provider.

## Interface

Each provider implements:

```python
def query(prompt: str, system_prompt: str | None = None) -> str:
    """Send a prompt and return the response text."""
    ...
```

## Default Settings

- **temperature**: 0.7 (configurable)
- **max_tokens**: 4096 (configurable)
- **timeout**: 60 seconds (configurable)

## Error Codes

| Code | Description |
|------|-------------|
| timeout | Request timed out |
| network | Connection/network error |
| rate_limit | Rate limit exceeded (429) |
| auth | Invalid or missing API key |
| api_error | Generic API error |
