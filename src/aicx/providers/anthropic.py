"""Anthropic provider."""

import os

from anthropic import Anthropic, APIConnectionError, APITimeoutError, RateLimitError

from aicx.providers.base import Provider, ProviderError


class AnthropicProvider(Provider):
    """Anthropic API provider."""

    name = "anthropic"

    def __init__(self, model_id: str = "claude-sonnet-4-20250514") -> None:
        """Initialize the Anthropic provider.

        Args:
            model_id: The model ID to use.

        Raises:
            ProviderError: If ANTHROPIC_API_KEY is not set.
        """
        self.model_id = model_id
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ProviderError(
                message="ANTHROPIC_API_KEY environment variable not set",
                provider=self.name,
                code="auth",
            )
        self._client = Anthropic(api_key=api_key)

    def query(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        timeout: int = 60,
    ) -> str:
        """Query Anthropic and return the response text."""
        messages = [{"role": "user", "content": prompt}]

        try:
            response = self._client.messages.create(
                model=self.model_id,
                system=system_prompt or "",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
            )

            if not response.content:
                raise ProviderError(
                    message="Empty response from Anthropic",
                    provider=self.name,
                    code="api_error",
                )

            # Anthropic returns content as a list of content blocks
            return response.content[0].text

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
