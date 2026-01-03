# AI Query Tool - Specification

## Goal

A simple tool that allows an AI agent (like Claude) to query other AI models and get their responses. The calling agent handles synthesis and artifact creation.

## How It Works

```
User → Claude: "Create a doc on the best way to cook pasta"
         ↓
Claude thinks: "I'll get perspectives from other models"
         ↓
Claude → Tool: query("How to cook pasta perfectly?", model="gpt-4o")
Claude → Tool: query("How to cook pasta perfectly?", model="gemini")
         ↓
Tool returns: GPT's answer, Gemini's answer
         ↓
Claude: Synthesizes all answers (including its own thinking) → Creates artifact
```

## Core Functionality

The tool does ONE thing: send a prompt to a specified model and return the response.

```bash
# CLI usage
aicx query "Your prompt here" --model gpt-4o
aicx query "Your prompt here" --model gemini-1.5-pro
aicx query "Your prompt here" --model claude-3-5-sonnet

# Returns the model's response as plain text
```

## MCP Tool Interface

For use as an MCP tool that Claude can invoke:

```json
{
  "name": "query_model",
  "description": "Query another AI model and get its response",
  "parameters": {
    "prompt": "The question or request to send",
    "model": "Model to query (gpt-4o, gemini-1.5-pro, claude-3-5-sonnet, etc.)",
    "system_prompt": "(optional) Custom system prompt"
  }
}
```

## Supported Models

| Alias | Provider | Model ID |
|-------|----------|----------|
| gpt-4o | OpenAI | gpt-4o |
| gpt-4-turbo | OpenAI | gpt-4-turbo |
| gemini | Google | gemini-1.5-pro |
| gemini-flash | Google | gemini-1.5-flash |
| claude-sonnet | Anthropic | claude-3-5-sonnet-20241022 |
| claude-opus | Anthropic | claude-3-opus-20240229 |

Custom model IDs can also be passed directly.

## Configuration

Environment variables for API keys:
```
OPENAI_API_KEY
ANTHROPIC_API_KEY
GEMINI_API_KEY
```

Optional config file (`~/.config/aicx/config.toml`):
```toml
[defaults]
timeout_seconds = 60
max_tokens = 4096
temperature = 0.7

[models.gpt-4o]
provider = "openai"
model_id = "gpt-4o"

[models.gemini]
provider = "google"
model_id = "gemini-1.5-pro"
```

## Error Handling

- Invalid API key → Clear error message with setup instructions
- Model not found → List available models
- Timeout → Return partial response if available, or error
- Rate limit → Return error with retry-after if available

## Non-Goals

- **No consensus logic** - The calling agent handles synthesis
- **No multi-round dialogue** - Single query/response per call
- **No artifact creation** - The calling agent creates files
- **No caching** - Each call is fresh
- **No conversation history** - Stateless tool

## Example Workflow

User asks Claude to research a topic:

1. User: "Compare the best approaches to state management in React"

2. Claude decides to gather multiple perspectives:
   - Calls `query_model(prompt="What are the best approaches to state management in React? Compare Redux, Zustand, Jotai, and Context API.", model="gpt-4o")`
   - Calls `query_model(prompt="...", model="gemini")`
   - Also formulates its own perspective

3. Claude receives responses from each model

4. Claude synthesizes all perspectives into a comprehensive comparison document

5. Claude creates the artifact for the user

## Implementation Phases

### Phase 1: Core Tool
- CLI with `query` command
- OpenAI provider adapter
- Basic error handling

### Phase 2: More Providers
- Anthropic adapter
- Google Gemini adapter
- Model alias system

### Phase 3: MCP Integration
- Package as MCP tool
- Structured output support
- Timeout/retry configuration
