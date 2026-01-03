# CLAUDE.md

## Project Overview

AI Query Tool (`aicx`) - A simple tool that allows an AI agent to query other AI models. The calling agent (e.g., Claude) handles synthesis and artifact creation.

**Status:** Early ideation phase. No code written yet.

## How It Works

```
User → Claude: "Create a doc on the best way to cook pasta"
         ↓
Claude → Tool: query("prompt", model="gpt-4o")
Claude → Tool: query("prompt", model="gemini")
         ↓
Claude: Synthesizes responses + own thinking → Creates artifact
```

The tool does ONE thing: send a prompt to a model, return the response.

## Source of Truth

**Primary reference:** `spec.md` - Complete specification for the tool.

## Feedback Protocol

When the user says "check for feedback" or similar, follow `docs/feedback-process.md`.

**Rules:**
- When making any changes to files in `docs/`, record those changes in `feedback/FEEDBACK_CLAUDE.md`
- Keep `feedback/FEEDBACK_CLAUDE.md` clean: remove resolved items when context changes
- Only keep active questions, comments, and concerns in the feedback file
- Separate latest feedback from previous feedback using `## Latest` and `## Previous` sections

## Directory Rules

| Directory | Rule |
|-----------|------|
| `claude/` | Claude-specific files (skills, reference docs) |
| `gpt/` | **NEVER read or modify** - GPT-specific files |
| `feedback/` | Feedback files for both agents |
| `docs/` | Shared documentation (record changes in feedback file) |
| `.claude/` | Claude Code configuration and slash commands |
| `AGENTS.md` | **NEVER modify** - Shared agent guidelines (read-only) |

## Slash Commands

- `/spec` - Review the full specification from `spec.md`
- `/feedback` - Check and respond to GPT feedback

## Project Structure (Planned)

```
src/aicx/
  __main__.py    # CLI entrypoint
  config.py      # Config loading
  providers/     # API adapters (openai, anthropic, google)
    base.py
    openai.py
    anthropic.py
    google.py
tests/
  test_*.py      # Pytest tests
```

## Commands

```bash
# Query a specific model
aicx query "Your prompt" --model gpt-4o
aicx query "Your prompt" --model gemini
aicx query "Your prompt" --model claude-sonnet

# Run tests
pytest

# Install for development
pip install -e .
```

## Supported Models

| Alias | Provider | Model ID |
|-------|----------|----------|
| gpt-4o | OpenAI | gpt-4o |
| gemini | Google | gemini-1.5-pro |
| claude-sonnet | Anthropic | claude-3-5-sonnet-20241022 |

## Provider Environment Variables

```
OPENAI_API_KEY
ANTHROPIC_API_KEY
GEMINI_API_KEY
```

## MCP Tool Interface

For use as an MCP tool:

```json
{
  "name": "query_model",
  "parameters": {
    "prompt": "The question to send",
    "model": "gpt-4o | gemini | claude-sonnet | etc."
  }
}
```

## Non-Goals

- No consensus logic (calling agent handles synthesis)
- No multi-round dialogue (single query/response)
- No caching
- No conversation history (stateless)

## Exit Codes

- 0: Success
- 1: Configuration error
- 2: Provider/network error
