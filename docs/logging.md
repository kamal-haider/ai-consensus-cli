# Logging and Audit Trail

## Default Behavior
- No logs by default.
- Only the final consensus answer is printed to stdout.

## Verbose Mode
- Enabled with `--verbose`.
- Logs are written to stderr as structured JSON lines.
- Each line includes `event`, `timestamp`, `round`, `model`, and `payload`.

## Redaction
- User prompt is logged as plain text in verbose mode.
- Provider credentials are never logged.
- Model raw responses can be stored if `verbose` is enabled.

## Events
- config_loaded
- round_started
- model_request
- model_response
- parse_recovery_attempt
- context_truncated
- mediator_update
- consensus_check
- run_complete
- error

## Retention
- The CLI does not write to disk by default.
- Users can pipe stderr to files when needed.
