"""Google Gemini provider."""

import os

from google import genai
from google.genai import types

from aicx.providers.base import Provider, ProviderError


class GeminiProvider(Provider):
    """Google Gemini API provider."""

    name = "gemini"

    def __init__(self, model_id: str = "gemini-1.5-pro") -> None:
        """Initialize the Gemini provider.

        Args:
            model_id: The model ID to use.

        Raises:
            ProviderError: If GEMINI_API_KEY is not set.
        """
        self.model_id = model_id
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ProviderError(
                message="GEMINI_API_KEY environment variable not set",
                provider=self.name,
                code="auth",
            )
        self._client = genai.Client(api_key=api_key)

    def query(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        timeout: int = 60,
    ) -> str:
        """Query Gemini and return the response text."""
        try:
            response = self._client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )

            if not response.text:
                raise ProviderError(
                    message="Empty response from Gemini",
                    provider=self.name,
                    code="api_error",
                )

            return response.text

        except (ConnectionError, TimeoutError) as e:
            raise ProviderError(
                message=f"Connection error: {e}",
                provider=self.name,
                code="network",
            ) from e
        except Exception as e:
            raise ProviderError(
                message=str(e),
                provider=self.name,
                code="api_error",
            ) from e
