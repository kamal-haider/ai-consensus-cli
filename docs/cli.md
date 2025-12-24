# CLI Interface

## Command
- aicx "your prompt"

## Flags
- --models: comma-separated list of model identifiers
- --mediator: model identifier
- --rounds: max number of rounds (default 3)
- --approval-ratio: fraction for consensus (default 0.67)
- --change-threshold: early stop threshold (default 0.10)
- --max-context-tokens: soft cap for total context; triggers summarization
- --verbose: enable audit trail
- --config: path to config file
- --share-mode: digest|raw
- --strict-json: disable JSON recovery and fail on first parse error
- --no-consensus-summary: omit disagreement summary

## Output
- Standard output: final candidate answer only.
- Standard error (verbose mode only): structured logs and diagnostics.

## Exit Codes
- 0: success (consensus or fallback).
- 1: configuration error.
- 2: provider error or zero successful responses.
- 3: consensus loop failed due to quorum with partial responses.
- 4: internal error.

## Performance and Cost (Estimates)
- Typical run (3 models, 2 rounds): ~20-40s, roughly $0.10-$0.30.
- Longer run (3 models, 3 rounds): ~40-60s, roughly $0.20-$0.50.
- Costs vary by model selection and response length.

## Examples
- aicx "Explain Rust ownership"
- aicx "Summarize this text" --models gpt-4o,claude-3-5 --rounds 2
