# Error Handling

## Principles
- Fail fast on configuration errors.
- Continue on individual model failures when quorum is met.
- Produce actionable error messages.

## Failure Modes
- ConfigError: invalid or missing config values.
- ProviderError: API failures, timeouts, invalid credentials.
- ParseError: malformed model output.
- QuorumError: insufficient successful responses.
- InternalError: unexpected exceptions.

## Retries
- No retries by default.
- Optional retries in config with exponential backoff (future).

## Timeouts
- Provider calls must respect `timeout_seconds`.
- Timeout counts as a failed response.

## Partial Failures
- If a participant fails, continue if quorum is satisfied.
- If mediator fails, abort.

## Zero Successful Responses
- If all participants fail, abort immediately with a ProviderError.
- The error message should enumerate failures per model.
- Exit code should be 2 for zero responses, 3 for below-quorum with some responses.
