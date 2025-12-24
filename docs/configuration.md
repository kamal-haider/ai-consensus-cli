# Configuration

## Location
- Default: `config/config.toml`
- Override with `--config`.

## Format (TOML)

Example:

```toml
[run]
max_rounds = 3
approval_ratio = 0.67
change_threshold = 0.10
share_mode = "digest"
max_context_tokens = 12000
strict_json = false
verbose = false

[[model]]
name = "gpt-4o"
provider = "openai"
model_id = "gpt-4o"
temperature = 0.2
max_tokens = 2048
timeout_seconds = 60
weight = 1.0

[[model]]
name = "claude-3-5"
provider = "anthropic"
model_id = "claude-3-5-sonnet-20241022"
temperature = 0.2
max_tokens = 2048
timeout_seconds = 60
weight = 1.0

[mediator]
name = "gpt-4o"
provider = "openai"
model_id = "gpt-4o"
```

## Notes
- `name` is a friendly alias used in CLI and logs.
- `model_id` is the provider-specific identifier passed to the API.
- If `max_context_tokens` is set, older rounds are truncated in v1 to stay within budget.
- `strict_json` disables JSON recovery and fails on any malformed output.

## Resolution Order
1) Defaults baked into code.
2) Config file values.
3) CLI overrides.

## Validation
- All model names must be unique.
- Mediator must reference a configured model and must not appear in the participant list.
- If a model entry is missing required fields, fail fast.

## Secrets
- API keys are read from environment variables.
- No secrets in config files.
