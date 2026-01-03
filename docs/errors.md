# Error Handling

## Exit Codes

| Code | Name | Description |
|------|------|-------------|
| 0 | SUCCESS | Query completed successfully |
| 1 | CONFIG_ERROR | Invalid configuration |
| 2 | PROVIDER_ERROR | API/network failure |

## Error Types

### ConfigError (Exit 1)
Invalid or missing configuration values.

**Examples:**
- `Configuration error: Unknown model 'foo'`
- `Configuration error: Missing OPENAI_API_KEY`

**Resolution:** Check config file and environment variables.

### ProviderError (Exit 2)
API failures, timeouts, or invalid credentials.

**Examples:**
- `Provider error (openai): Invalid API key`
- `Provider error (anthropic): Request timeout after 60s`
- `Provider error (gemini): Rate limit exceeded`

**Resolution:** Verify API keys, check network connectivity, review rate limits.

## Error Codes

| Code | Description | Retryable |
|------|-------------|-----------|
| timeout | Request timed out | Yes |
| network | Connection error | Yes |
| rate_limit | Rate limit (429) | Yes |
| auth | Invalid API key (401/403) | No |
| api_error | Generic API error | No |

## Verbose Mode

Use `--verbose` to see detailed error information:

```bash
aicx query "prompt" --model gpt-4o --verbose
```
