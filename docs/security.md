# Security and Safety

## Threat Model
- Prompt injection within user input.
- Malformed provider responses.
- Accidental leakage of API keys.

## Controls
- Strict output parsing and validation.
- Separation of config and secrets.
- Redaction of credentials in logs.

## Data Handling
- No disk persistence by default.
- Users opt-in to audit logs via stderr.

## Safety Limits
- Limit max tokens per model.
- Limit total rounds.
- Enforce timeouts per call.

## False Consensus Risk
- Multiple models can agree on incorrect or outdated information.
- For high-stakes decisions, users should independently verify outputs.
