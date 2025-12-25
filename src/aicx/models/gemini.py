"""Gemini provider adapter with JSON mode support."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

from google import genai
from google.genai import types

from aicx.models.errors import map_api_error, map_network_error, map_parse_error
from aicx.types import ModelConfig, ParseError, PromptRequest, ProviderError, Response


@dataclass
class GeminiProvider:
    """Gemini provider adapter.

    Implements the ProviderAdapter protocol for Google's Gemini models.
    Supports JSON mode via response_mime_type configuration.
    """

    name: str = "gemini"
    supports_json: bool = True
    model_config: ModelConfig | None = None
    _client: genai.Client | None = None

    def __post_init__(self) -> None:
        """Initialize the Gemini client."""
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ProviderError(
                "GEMINI_API_KEY or GOOGLE_API_KEY environment variable not set",
                provider=self.name,
                code="auth",
            )
        self._client = genai.Client(api_key=api_key)

    def create_chat_completion(self, request: PromptRequest) -> Response:
        """Send a chat completion request to Gemini.

        Args:
            request: The prompt request containing user prompt, system prompt, etc.

        Returns:
            Response object with model output parsed from JSON.

        Raises:
            ProviderError: On network/timeout/API errors or missing API key.
            ParseError: On malformed JSON output.
        """
        if self._client is None:
            raise ProviderError(
                "Gemini client not initialized",
                provider=self.name,
                code="config",
            )

        # Get model configuration
        if self.model_config is None:
            raise ProviderError(
                "ModelConfig not provided to GeminiProvider",
                provider=self.name,
                code="config",
            )

        model_id = self.model_config.model_id
        temperature = self.model_config.temperature
        max_tokens = self.model_config.max_tokens
        timeout_seconds = self.model_config.timeout_seconds

        try:
            # Generate content with JSON mode
            response = self._client.models.generate_content(
                model=model_id,
                contents=request.user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=request.system_prompt,
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    response_mime_type="application/json",
                ),
            )

            # Extract the text response
            if not response.text:
                raise ParseError(
                    "Empty response from Gemini",
                    raw_output="",
                )

            raw_output = response.text

            # Parse the JSON response
            try:
                parsed = json.loads(raw_output)
            except json.JSONDecodeError as e:
                raise map_parse_error(
                    raw_output,
                    f"Invalid JSON: {e}",
                )

            # Extract fields from the parsed JSON
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

        except (ConnectionError, TimeoutError) as e:
            raise map_network_error(e, self.name)
        except ParseError:
            raise
        except ProviderError:
            raise
        except Exception as e:
            raise map_api_error(e, self.name)


def create_gemini_provider(model_config: ModelConfig) -> GeminiProvider:
    """Create a Gemini provider adapter.

    Args:
        model_config: The model configuration containing model ID, temperature, etc.

    Returns:
        A configured GeminiProvider instance.
    """
    return GeminiProvider(model_config=model_config)
