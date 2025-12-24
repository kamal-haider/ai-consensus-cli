# Provider Adapters

## Interface Contract
Each provider adapter implements:
- name: provider identifier
- supports_json: bool
- create_chat_completion(request: PromptRequest) -> Response

## Adapter Responsibilities
- Map PromptRequest into provider-specific API calls.
- Enforce timeout and max_tokens.
- Return a Response with the `raw` field when verbose is enabled.

## Error Mapping
- Network errors -> ProviderError.
- Timeout -> ProviderError with code "timeout".
- Malformed output -> ParseError.

## Environment Variables
- OPENAI_API_KEY
- ANTHROPIC_API_KEY
- GEMINI_API_KEY

## Model Names and Aliases
- `name` is a friendly alias (used in CLI and logs).
- `model_id` is passed to the provider API.
- The system should accept a small alias table and pass through unknown names verbatim.
- Aliases should be stable; users can opt into newer versions by setting `model_id` explicitly.

Alias table (initial):
- gpt-4o -> gpt-4o
- claude-3-5 -> claude-3-5-sonnet-20241022
- gemini-1.5-pro -> gemini-1.5-pro
- gemini-1.5-flash -> gemini-1.5-flash

## JSON Mode Support
- OpenAI: response_format json_object
- Gemini: response_mime_type application/json
- Anthropic: prompt-only JSON compliance

## Rate Limiting
- No global limiter in v1.
- Adapters should surface rate limit errors clearly.

## Deterministic Settings
- temperature default 0.2.
- set top_p = 1.0 where supported to reduce sampling variance.
- top_p, frequency_penalty, and other params unset unless configured.
