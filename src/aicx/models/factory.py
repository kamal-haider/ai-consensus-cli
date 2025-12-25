"""Provider factory for instantiating model providers."""

from __future__ import annotations

from typing import Callable

from aicx.models.mock import MockProvider
from aicx.models.registry import ProviderAdapter
from aicx.retry.wrapper import wrap_with_retry
from aicx.types import ModelConfig, ProviderError


# Provider factory functions mapping
_PROVIDER_FACTORIES: dict[str, Callable[[ModelConfig], ProviderAdapter]] = {}


def _register_provider(name: str, factory: Callable[[ModelConfig], ProviderAdapter]) -> None:
    """Register a provider factory function.

    Args:
        name: Provider name (e.g., "openai", "anthropic", "gemini").
        factory: Factory function that creates the provider.
    """
    _PROVIDER_FACTORIES[name] = factory


def _create_mock_from_config(model_config: ModelConfig) -> MockProvider:
    """Create a mock provider from ModelConfig.

    Args:
        model_config: Model configuration.

    Returns:
        Configured MockProvider instance.
    """
    return MockProvider(name=model_config.name)


def _register_builtin_providers() -> None:
    """Register all built-in provider factories."""
    # Import here to avoid circular imports and allow lazy loading
    from aicx.models.openai import create_openai_provider
    from aicx.models.anthropic import create_anthropic_provider
    from aicx.models.gemini import create_gemini_provider

    _register_provider("openai", create_openai_provider)
    _register_provider("anthropic", create_anthropic_provider)
    _register_provider("gemini", create_gemini_provider)
    _register_provider("mock", _create_mock_from_config)


def create_provider(model_config: ModelConfig) -> ProviderAdapter:
    """Create a provider instance based on model configuration.

    Args:
        model_config: Configuration for the model including provider name.

    Returns:
        Configured provider adapter.

    Raises:
        ProviderError: If the provider is not registered.
    """
    # Lazy registration of built-in providers
    if not _PROVIDER_FACTORIES:
        _register_builtin_providers()

    provider_name = model_config.provider.lower()

    if provider_name not in _PROVIDER_FACTORIES:
        raise ProviderError(
            f"Unknown provider: {provider_name}. "
            f"Available providers: {', '.join(sorted(_PROVIDER_FACTORIES.keys()))}",
            provider=provider_name,
            code="config",
        )

    factory = _PROVIDER_FACTORIES[provider_name]
    provider = factory(model_config)

    # Wrap with retry if configured
    if model_config.retry is not None:
        provider = wrap_with_retry(provider, model_config.retry)

    return provider


def create_providers(configs: tuple[ModelConfig, ...]) -> dict[str, ProviderAdapter]:
    """Create providers for multiple model configurations.

    Args:
        configs: Tuple of model configurations.

    Returns:
        Dictionary mapping model names to their providers.

    Raises:
        ProviderError: If any provider cannot be created.
    """
    providers = {}
    for config in configs:
        providers[config.name] = create_provider(config)
    return providers


def get_available_providers() -> list[str]:
    """Get list of available provider names.

    Returns:
        List of registered provider names.
    """
    if not _PROVIDER_FACTORIES:
        _register_builtin_providers()
    return sorted(_PROVIDER_FACTORIES.keys())
