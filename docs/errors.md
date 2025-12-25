# Error Handling

## Principles
- Fail fast on configuration errors.
- Continue on individual model failures when quorum is met.
- Produce actionable error messages with clear next steps.

## Exit Codes

| Code | Name | Description | Common Causes |
|------|------|-------------|---------------|
| 0 | SUCCESS | Consensus reached or best-effort answer | Normal operation |
| 1 | CONFIG_ERROR | Invalid configuration | Missing config file, invalid TOML, bad flag values |
| 2 | PROVIDER_ERROR | API/network failure | Invalid API keys, network issues, all models failed |
| 3 | QUORUM_ERROR | Insufficient responses | Some models failed, remaining below threshold |
| 4 | INTERNAL_ERROR | Unexpected exception | Bug in code, unexpected API response |

## Error Types

### ConfigError (Exit 1)
Invalid or missing configuration values.

**Examples:**
- `Configuration error: Model 'unknown' not found in config`
- `Configuration error: approval_ratio must be between 0 and 1`
- `Configuration error: Mediator cannot also be a participant model`

**Resolution:** Check config file syntax and flag values.

### ProviderError (Exit 2)
API failures, timeouts, or invalid credentials.

**Examples:**
- `Provider error (openai): Invalid API key`
- `Provider error (anthropic): Request timeout after 60s`
- `Provider error: All models failed - no responses received`

**Resolution:** Verify API keys, check network connectivity, review rate limits.

### QuorumError (Exit 3)
Some responses received, but below the required threshold.

**Examples:**
- `Quorum error: Received 1 of 3 responses (need 2 for quorum)`
- `Insufficient responses in round 2: 1 received, 2 required`

**Resolution:** Check failing model logs, consider lowering --approval-ratio.

### ParseError (Exit 2)
Malformed model output that could not be recovered.

**Examples:**
- `Parse error (gpt-4o): Invalid JSON in response`
- `Parse error: Missing required field 'answer'`

**Resolution:** Use --verbose to see raw responses, consider --strict-json for debugging.

### ZeroResponseError (Exit 2)
All participant models failed in a round.

**Examples:**
- `All models failed in round 1: gpt-4o (timeout), claude-3-5 (rate_limit)`

**Resolution:** Check API keys and rate limits for all providers.

## Retries

Retry behavior is configured per-model in the config file:

```toml
[[model]]
name = "gpt-4o"
provider = "openai"
model_id = "gpt-4o"

[model.retry]
max_attempts = 3
base_delay = 1.0
max_delay = 30.0
```

**Retry policy:**
- Retryable errors: timeout, network errors, rate limits (429), server errors (5xx)
- Non-retryable errors: authentication (401), bad request (400), not found (404)
- Backoff: exponential with jitter (base_delay * 2^attempt + random 0-25%)

## Timeouts

- Provider calls respect `timeout_seconds` from model config (default: 60s)
- Timeout counts as a failed response (retryable if configured)
- Mediator timeout aborts the run immediately

## Partial Failures

- If a participant fails but quorum is met, the run continues
- Failed models are tracked in metadata and can be seen with --verbose
- If mediator fails, the run aborts (exit code 2)

## Verbose Mode

Use `--verbose` to get detailed diagnostics:

```bash
aicx "your prompt" --verbose 2>debug.log
```

The JSONL audit log includes:
- `model_request`: each API call with prompt length
- `model_response`: each response with timing
- `retry_attempt`: retry attempts with delay
- `error`: detailed error information with stack traces
