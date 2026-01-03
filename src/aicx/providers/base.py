"""Base provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ProviderError(Exception):
    """Error from a provider."""

    message: str
    provider: str
    code: str  # timeout, network, rate_limit, auth, api_error

    def __str__(self) -> str:
        return f"Provider error ({self.provider}): {self.message}"


class Provider(ABC):
    """Base class for AI model providers."""

    name: str

    @abstractmethod
    def query(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        timeout: int = 60,
    ) -> str:
        """Query the model and return the response text.

        Args:
            prompt: The user prompt to send.
            system_prompt: Optional system prompt.
            temperature: Sampling temperature (0.0-2.0).
            max_tokens: Maximum tokens in response.
            timeout: Request timeout in seconds.

        Returns:
            The model's response as a string.

        Raises:
            ProviderError: On API/network errors.
        """
        ...
