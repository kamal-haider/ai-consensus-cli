"""Anthropic provider adapter."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

from anthropic import Anthropic, APIConnectionError, APITimeoutError, APIError

from aicx.models.errors import map_api_error, map_network_error, map_parse_error
from aicx.types import ModelConfig, ParseError, PromptRequest, ProviderError, Response


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
            # Build the API request
            # Anthropic uses system as a separate parameter
            response = self._client.messages.create(
                model=self.model_config.model_id,
                system=request.system_prompt,
                messages=[{"role": "user", "content": request.user_prompt}],
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

            raw_output = response.content[0].text

            # Parse the JSON response
            try:
                parsed = json.loads(raw_output)
            except json.JSONDecodeError as e:
                raise map_parse_error(raw_output, f"Invalid JSON: {e}")

            # Extract fields from parsed JSON
            answer = parsed.get("answer", "")

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
