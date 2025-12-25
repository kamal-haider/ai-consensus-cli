"""Gemini provider adapter with JSON mode support."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

import google.generativeai as genai

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
        # Get API key from environment
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ProviderError(
                "GEMINI_API_KEY environment variable not set",
                provider=self.name,
                code="auth",
            )

        # Configure the Gemini client
        genai.configure(api_key=api_key)

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
            # Create the generative model with JSON mode
            model = genai.GenerativeModel(
                model_name=model_id,
                generation_config=genai.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    response_mime_type="application/json",
                ),
            )

            # Combine system and user prompts
            # Gemini doesn't have a separate system message in the same way,
            # so we prepend the system prompt to the user prompt
            combined_prompt = f"{request.system_prompt}\n\n{request.user_prompt}"

            # Generate content with timeout
            response = model.generate_content(
                combined_prompt,
                request_options={"timeout": timeout_seconds},
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
