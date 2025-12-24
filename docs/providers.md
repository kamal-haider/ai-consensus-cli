# Provider Adapters

## Interface Contract (Protocol)
Each provider adapter implements the `ProviderAdapter` protocol defined in `src/aicx/models/registry.py`:

```python
class ProviderAdapter(Protocol):
    name: str           # Provider identifier (e.g., "openai", "anthropic", "gemini")
    supports_json: bool # Whether native JSON mode is supported

    def create_chat_completion(self, request: PromptRequest) -> Response:
        """Send a chat completion request to the provider."""
        ...
```

## Implemented Adapters

### OpenAI (`src/aicx/models/openai.py`)
- **Class**: `OpenAIProvider`
- **Factory**: `create_openai_provider(model_config: ModelConfig)`
- **JSON Mode**: `response_format={"type": "json_object"}` (native support)
- **API Pattern**: `client.chat.completions.create()`
- **System Prompt**: Passed in messages array with `role: "system"`

### Anthropic (`src/aicx/models/anthropic.py`)
- **Class**: `AnthropicProvider`
- **Factory**: `create_anthropic_provider(model_config: ModelConfig)`
- **JSON Mode**: Prompt-based compliance only (`supports_json=False`)
- **API Pattern**: `client.messages.create()`
- **System Prompt**: Passed as separate `system` parameter (not in messages)

### Gemini (`src/aicx/models/gemini.py`)
- **Class**: `GeminiProvider`
- **Factory**: `create_gemini_provider(model_config: ModelConfig)`
- **JSON Mode**: `response_mime_type="application/json"` in `GenerationConfig`
- **API Pattern**: `model.generate_content()`
- **System Prompt**: Prepended to user prompt (Gemini doesn't have separate system message)

### Mock (`src/aicx/models/mock.py`)
- **Class**: `MockProvider`
- **Factories**: `create_mock_provider()`, `create_echo_provider()`, `create_approving_provider()`, `create_objecting_provider()`
- Used for testing without real API calls

## Adapter Responsibilities
- Map PromptRequest into provider-specific API calls.
- Enforce timeout and max_tokens from ModelConfig.
- Return a Response with the `raw` field populated.
- Set `top_p=1.0` for reduced sampling variance.

## Error Mapping (`src/aicx/models/errors.py`)
All adapters use shared error mapping utilities:
- `map_network_error(exc, provider)` -> ProviderError with code "network" or "timeout"
- `map_api_error(exc, provider)` -> ProviderError with appropriate code
- `map_parse_error(output, reason)` -> ParseError with raw output

Error codes:
- `timeout` - Request timed out
- `network` - Connection/network error
- `rate_limit` - Rate limit exceeded (429)
- `auth` - Authentication error (401/403)
- `service_unavailable` - Service unavailable (503)
- `api_error` - Generic API error
- `config` - Configuration error

## Environment Variables
- `OPENAI_API_KEY` - Required for OpenAI adapter
- `ANTHROPIC_API_KEY` - Required for Anthropic adapter
- `GEMINI_API_KEY` - Required for Gemini adapter

Missing API keys raise `ProviderError` with `code="auth"` at provider initialization.

## Model Names and Aliases
Defined in `src/aicx/models/registry.py`:
- `name` is a friendly alias (used in CLI and logs).
- `model_id` is passed to the provider API.
- The alias table passes through unknown names verbatim.

Alias table:
- gpt-4o -> gpt-4o
- claude-3-5 -> claude-3-5-sonnet-20241022
- gemini-1.5-pro -> gemini-1.5-pro
- gemini-1.5-flash -> gemini-1.5-flash

## JSON Mode Support Summary
| Provider | Native JSON Mode | Implementation |
|----------|-----------------|----------------|
| OpenAI | Yes | `response_format={"type": "json_object"}` |
| Gemini | Yes | `response_mime_type="application/json"` |
| Anthropic | No | Prompt-based compliance |

## Deterministic Settings
All adapters apply:
- `temperature`: from ModelConfig (default 0.2)
- `top_p=1.0`: reduces sampling variance
- `max_tokens`: from ModelConfig
- `timeout`: from ModelConfig (in seconds)

## Rate Limiting
- No global limiter in v1.
- Rate limit errors are surfaced as `ProviderError` with `code="rate_limit"`.
