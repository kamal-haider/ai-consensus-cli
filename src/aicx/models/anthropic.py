"""Anthropic provider adapter."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass

from anthropic import Anthropic, APIConnectionError, APITimeoutError, APIError

from aicx.models.errors import map_api_error, map_network_error, map_parse_error
from aicx.types import ModelConfig, ParseError, PromptRequest, ProviderError, Response


def _extract_json(text: str) -> str:
    """Extract JSON from text that may contain markdown or surrounding text.

    Args:
        text: Raw text that may contain JSON.

    Returns:
        Extracted JSON string.

    Raises:
        ParseError: If no valid JSON can be extracted.
    """
    # If it's already valid JSON, return as-is
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return text

    # Try to extract from markdown code block
    # Match ```json ... ``` or ``` ... ```
    code_block_pattern = r"```(?:json)?\s*\n?(.*?)\n?```"
    match = re.search(code_block_pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Try to find JSON object in the text
    # Look for first { and last }
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return text[first_brace : last_brace + 1]

    # Return original if no extraction possible
    return text


@dataclass
class AnthropicProvider:
    """Anthropic provider adapter.

    Uses prompt-based JSON compliance (no native JSON mode).
    Reads API key from ANTHROPIC_API_KEY environment variable.
    """

    name: str = "anthropic"
    supports_json: bool = False  # Anthropic uses prompt-based JSON compliance
    model_config: ModelConfig | None = None
    _client: Anthropic | None = None

    def __post_init__(self) -> None:
        """Initialize the Anthropic client."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ProviderError(
                "ANTHROPIC_API_KEY environment variable not set",
                provider=self.name,
                code="auth",
            )
        self._client = Anthropic(api_key=api_key)

    def create_chat_completion(self, request: PromptRequest) -> Response:
        """Send a chat completion request to Anthropic.

        Args:
            request: The prompt request containing user prompt, system prompt, etc.

        Returns:
            Response object with model output.

        Raises:
            ProviderError: On network/timeout/API errors.
            ParseError: On malformed model output.
        """
        if self._client is None:
            raise ProviderError(
                "Anthropic client not initialized",
                provider=self.name,
                code="internal",
            )

        if self.model_config is None:
            raise ProviderError(
                "ModelConfig not provided to AnthropicProvider",
                provider=self.name,
                code="config",
            )

        try:
            # Build messages with prefill to encourage JSON output
            # Prefill starts the assistant response with "{" to force JSON
            messages = [
                {"role": "user", "content": request.user_prompt},
                {"role": "assistant", "content": "{"},
            ]

            # Build the API request
            # Anthropic uses system as a separate parameter
            response = self._client.messages.create(
                model=self.model_config.model_id,
                system=request.system_prompt,
                messages=messages,
                temperature=self.model_config.temperature,
                max_tokens=self.model_config.max_tokens,
                timeout=self.model_config.timeout_seconds,
                top_p=1.0,  # Reduce sampling variance
            )

            # Extract the text content from the response
            # Anthropic returns content as a list of content blocks
            if not response.content:
                raise ParseError(
                    "Empty response from Anthropic",
                    raw_output=str(response),
                )

            # Reconstruct JSON by prepending the prefill "{"
            raw_output = "{" + response.content[0].text

            # Extract JSON from potential markdown or surrounding text
            json_str = _extract_json(raw_output)

            # Parse the JSON response
            try:
                parsed = json.loads(json_str)
            except json.JSONDecodeError as e:
                raise map_parse_error(raw_output, f"Invalid JSON: {e}")

            # Extract fields from parsed JSON
            # Ensure answer is a string (serialize if it's a list/dict)
            answer = parsed.get("answer", "")
            if not isinstance(answer, str):
                answer = json.dumps(answer, indent=2)

            return Response(
                model_name=self.model_config.name,
                answer=answer,
                approve=parsed.get("approve"),
                critical=parsed.get("critical"),
                objections=tuple(parsed.get("objections", [])),
                missing=tuple(parsed.get("missing", [])),
                edits=tuple(parsed.get("edits", [])),
                confidence=parsed.get("confidence"),
                raw=raw_output,
            )

        except APITimeoutError as e:
            raise ProviderError(
                f"Request to {self.name} timed out: {e}",
                provider=self.name,
                code="timeout",
            ) from e
        except APIConnectionError as e:
            raise map_network_error(e, self.name) from e
        except APIError as e:
            raise map_api_error(e, self.name) from e
        except (ParseError, ProviderError):
            # Re-raise our own exceptions
            raise
        except Exception as e:
            # Catch any other unexpected errors
            raise ProviderError(
                f"Unexpected error from {self.name}: {e}",
                provider=self.name,
                code="internal",
            ) from e


def create_anthropic_provider(model_config: ModelConfig) -> AnthropicProvider:
    """Create an Anthropic provider adapter.

    Args:
        model_config: Configuration for the model.

    Returns:
        AnthropicProvider instance.

    Raises:
        ProviderError: If ANTHROPIC_API_KEY is not set.
    """
    return AnthropicProvider(model_config=model_config)
