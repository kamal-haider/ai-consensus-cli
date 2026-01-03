"""OpenAI provider."""

import os

from openai import APIConnectionError, APITimeoutError, OpenAI, RateLimitError

from aicx.providers.base import Provider, ProviderError


class OpenAIProvider(Provider):
    """OpenAI API provider."""

    name = "openai"

    def __init__(self, model_id: str = "gpt-4o") -> None:
        """Initialize the OpenAI provider.

        Args:
            model_id: The model ID to use (e.g., "gpt-4o").

        Raises:
            ProviderError: If OPENAI_API_KEY is not set.
        """
        self.model_id = model_id
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ProviderError(
                message="OPENAI_API_KEY environment variable not set",
                provider=self.name,
                code="auth",
            )
        self._client = OpenAI(api_key=api_key)

    def query(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        timeout: int = 60,
    ) -> str:
        """Query OpenAI and return the response text."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self._client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
            )

            if not response.choices:
                raise ProviderError(
                    message="No response choices returned",
                    provider=self.name,
                    code="api_error",
                )

            content = response.choices[0].message.content
            return content if content else ""

        except APITimeoutError as e:
            raise ProviderError(
                message=f"Request timed out: {e}",
                provider=self.name,
                code="timeout",
            ) from e
        except APIConnectionError as e:
            raise ProviderError(
                message=f"Connection error: {e}",
                provider=self.name,
                code="network",
            ) from e
        except RateLimitError as e:
            raise ProviderError(
                message=f"Rate limit exceeded: {e}",
                provider=self.name,
                code="rate_limit",
            ) from e
        except Exception as e:
            raise ProviderError(
                message=str(e),
                provider=self.name,
                code="api_error",
            ) from e
