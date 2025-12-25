# CLI Interface

## Command

```bash
aicx "your prompt"
```

## Options

### Model Selection
| Flag | Description |
|------|-------------|
| `--models LIST` | Comma-separated model names for participants (e.g., `gpt-4o,claude-3-5`) |
| `--mediator NAME` | Model name for mediator (must differ from participants) |

### Consensus Parameters
| Flag | Default | Description |
|------|---------|-------------|
| `--rounds N` | 3 | Maximum consensus rounds before stopping |
| `--approval-ratio RATIO` | 0.67 | Fraction of approvals needed (0.0-1.0) |
| `--change-threshold RATIO` | 0.10 | Minimum change to continue iterating |

### Context Management
| Flag | Description |
|------|-------------|
| `--max-context-tokens N` | Token budget; older rounds truncated when exceeded |

### Behavior
| Flag | Description |
|------|-------------|
| `--share-mode {digest,raw}` | How responses are shared between rounds |
| `--strict-json` | Fail on JSON parse errors (no recovery) |
| `--verbose` | Write JSONL audit log to stderr |
| `--no-consensus-summary` | Suppress disagreement summary |

### Configuration
| Flag | Description |
|------|-------------|
| `--config PATH` | Path to TOML config file (default: `config/config.toml`) |
| `--version` | Show version and exit |

## Output

### Standard Output
The final consensus answer, optionally followed by a disagreement summary if consensus was not reached.

**With consensus:**
```
The answer to your question is...
```

**Without consensus:**
```
The answer to your question is...

---
Consensus: NOT REACHED (2/3 approvals, 1 critical objection)
Confidence: MEDIUM

Unresolved Issues:
- Critical: The calculation appears incorrect
- Missing: No citation provided for the claim
```

### Standard Error (verbose mode)
Structured JSONL logs for debugging and auditing.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (consensus or best-effort answer) |
| 1 | Configuration error |
| 2 | Provider error or zero successful responses |
| 3 | Quorum failure (some responses, but below threshold) |
| 4 | Internal error |

## Examples

### Basic Usage
```bash
aicx "Explain Rust ownership"
```

### Specific Models
```bash
aicx "Summarize this text" --models gpt-4o,claude-3-5 --rounds 2
```

### Quick Consensus
```bash
aicx "Simple question" --approval-ratio 0.5 --rounds 1
```

### Debugging
```bash
aicx "Complex analysis" --verbose 2>debug.log
```

### With Context Limit
```bash
aicx "Long document analysis" --max-context-tokens 8000
```

### Strict Mode
```bash
aicx "Structured output" --strict-json
```

## Performance and Cost Estimates

| Scenario | Time | Cost |
|----------|------|------|
| 3 models, 2 rounds | ~20-40s | ~$0.10-$0.30 |
| 3 models, 3 rounds | ~40-60s | ~$0.20-$0.50 |

Costs vary by model selection and response length.
