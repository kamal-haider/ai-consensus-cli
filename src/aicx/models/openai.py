"""OpenAI provider adapter."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

from openai import APIConnectionError, APITimeoutError, OpenAI, RateLimitError

from aicx.models.errors import handle_provider_exception, map_parse_error
from aicx.types import ModelConfig, ParseError, PromptRequest, ProviderError, Response


@dataclass
class OpenAIProvider:
    """OpenAI provider adapter.

    Supports JSON mode via response_format={"type": "json_object"}.
    Reads API key from OPENAI_API_KEY environment variable.
    """

    name: str = "openai"
    supports_json: bool = True
    model_config: ModelConfig | None = None
    _client: OpenAI | None = None

    def __post_init__(self) -> None:
        """Initialize the OpenAI client."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ProviderError(
                "OPENAI_API_KEY environment variable not set",
                provider=self.name,
                code="auth",
            )
        self._client = OpenAI(api_key=api_key)

    def create_chat_completion(self, request: PromptRequest) -> Response:
        """Send a chat completion request to OpenAI.

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
                "OpenAI client not initialized",
                provider=self.name,
                code="internal",
            )

        if self.model_config is None:
            raise ProviderError(
                "ModelConfig not provided to OpenAIProvider",
                provider=self.name,
                code="config",
            )

        # Build messages
        messages = [
            {"role": "system", "content": request.system_prompt},
            {"role": "user", "content": request.user_prompt},
        ]

        # Prepare API call parameters
        api_params: dict = {
            "model": self.model_config.model_id,
            "messages": messages,
            "temperature": self.model_config.temperature,
            "max_tokens": self.model_config.max_tokens,
            "timeout": self.model_config.timeout_seconds,
            "top_p": 1.0,  # Reduce sampling variance
        }

        # Use JSON mode if supported
        if self.supports_json:
            api_params["response_format"] = {"type": "json_object"}

        try:
            # Call OpenAI API
            completion = self._client.chat.completions.create(**api_params)

            # Extract response content
            if not completion.choices:
                raise ParseError(
                    "No choices in completion response",
                    raw_output=str(completion),
                )

            raw_content = completion.choices[0].message.content
            if raw_content is None:
                raise ParseError(
                    "Empty content in completion response",
                    raw_output=str(completion),
                )

            # Parse JSON response
            try:
                parsed = json.loads(raw_content)
            except json.JSONDecodeError as e:
                raise map_parse_error(raw_content, f"Invalid JSON: {e}")

            # Extract fields from parsed JSON
            answer = parsed.get("answer", "")

            # Build Response object
            return Response(
                model_name=self.model_config.name,
                answer=answer,
                approve=parsed.get("approve"),
                critical=parsed.get("critical"),
                objections=tuple(parsed.get("objections", [])),
                missing=tuple(parsed.get("missing", [])),
                edits=tuple(parsed.get("edits", [])),
                confidence=parsed.get("confidence"),
                raw=raw_content,
            )

        except APITimeoutError as e:
            raise ProviderError(
                f"Request to {self.name} timed out: {e}",
                provider=self.name,
                code="timeout",
            ) from e
        except APIConnectionError as e:
            raise ProviderError(
                f"Network error connecting to {self.name}: {e}",
                provider=self.name,
                code="network",
            ) from e
        except RateLimitError as e:
            raise ProviderError(
                f"Rate limit exceeded for {self.name}: {e}",
                provider=self.name,
                code="rate_limit",
            ) from e
        except (ParseError, ProviderError):
            # Re-raise our own exceptions
            raise
        except Exception as e:
            # Catch-all for other API errors
            raise handle_provider_exception(e, self.name)


def create_openai_provider(model_config: ModelConfig) -> OpenAIProvider:
    """Create an OpenAI provider instance.

    Args:
        model_config: Configuration for the model.

    Returns:
        Configured OpenAIProvider instance.

    Raises:
        ProviderError: If OPENAI_API_KEY is not set.
    """
    return OpenAIProvider(model_config=model_config)
