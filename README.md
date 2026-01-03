# AI Query Tool

A simple CLI/MCP tool that allows an AI agent to query other AI models.

## How It Works

```
User → Claude: "Create a doc on cooking pasta"
         ↓
Claude → Tool: query("prompt", model="gpt-4o")
Claude → Tool: query("prompt", model="gemini")
         ↓
Claude: Synthesizes responses → Creates artifact
```

The tool does one thing: send a prompt to a model, return the response. The calling agent handles synthesis.

## Usage

```bash
# Query a model
aicx query "Your prompt here" --model gpt-4o
aicx query "Your prompt here" --model gemini
aicx query "Your prompt here" --model claude-sonnet
```

## Setup

Set API keys as environment variables:
```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GEMINI_API_KEY="..."
```

## Documentation

- `spec.md` - Full specification
- `docs/` - Additional documentation
- `CLAUDE.md` - Instructions for Claude Code
