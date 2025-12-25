"""Provider registry and adapter interface."""

from __future__ import annotations

from typing import Protocol

from aicx.types import PromptRequest, Response


# Model alias table: friendly names -> provider model IDs
MODEL_ALIASES: dict[str, str] = {
    "gpt-4o": "gpt-4o",
    "claude-3-5": "claude-sonnet-4-20250514",
    "gemini-1.5-pro": "gemini-1.5-pro",
    "gemini-1.5-flash": "gemini-1.5-flash",
    "gemini-2": "gemini-2.0-flash-exp",
}


class ProviderAdapter(Protocol):
    """Protocol for provider adapters.

    Each provider adapter implements:
    - name: provider identifier
    - supports_json: bool indicating JSON mode support
    - create_chat_completion: method to send request and return response
    """

    name: str
    supports_json: bool

    def create_chat_completion(self, request: PromptRequest) -> Response:
        """Send a chat completion request to the provider.

        Args:
            request: The prompt request containing user prompt, system prompt, etc.

        Returns:
            Response object with model output.

        Raises:
            ProviderError: On network/timeout/API errors.
            ParseError: On malformed model output.
        """
        ...


class ProviderRegistry:
    """Registry for provider adapters with model name resolution."""

    def __init__(self) -> None:
        self._providers: dict[str, ProviderAdapter] = {}

    def register(self, provider: ProviderAdapter) -> None:
        """Register a provider adapter.

        Args:
            provider: The provider adapter to register.
        """
        self._providers[provider.name] = provider

    def get(self, name: str) -> ProviderAdapter:
        """Get a provider adapter by name.

        Args:
            name: The provider name.

        Returns:
            The provider adapter.

        Raises:
            KeyError: If the provider is not registered.
        """
        if name not in self._providers:
            raise KeyError(f"Unknown provider: {name}")
        return self._providers[name]

    def resolve_model_id(self, name: str) -> str:
        """Resolve a model name to its provider model ID.

        If the name is in the alias table, return the mapped ID.
        Otherwise, pass through the name verbatim.

        Args:
            name: The model name or alias.

        Returns:
            The resolved model ID.
        """
        return MODEL_ALIASES.get(name, name)

    def list_providers(self) -> list[str]:
        """List all registered provider names.

        Returns:
            List of provider names.
        """
        return list(self._providers.keys())


def default_registry() -> ProviderRegistry:
    """Create a default provider registry.

    Returns:
        An empty registry (real providers registered elsewhere).
    """
    return ProviderRegistry()
