"""Provider registry and model alias resolution."""

from aicx.providers.base import Provider, ProviderError

# Model aliases: friendly name -> (provider, model_id)
MODEL_REGISTRY: dict[str, tuple[str, str]] = {
    # OpenAI
    "gpt-4o": ("openai", "gpt-4o"),
    "gpt-4-turbo": ("openai", "gpt-4-turbo"),
    "gpt-3.5-turbo": ("openai", "gpt-3.5-turbo"),
    # Anthropic
    "claude-sonnet": ("anthropic", "claude-sonnet-4-20250514"),
    "claude-3-5-sonnet": ("anthropic", "claude-3-5-sonnet-20241022"),
    "claude-opus": ("anthropic", "claude-3-opus-20240229"),
    "claude-haiku": ("anthropic", "claude-3-haiku-20240307"),
    # Google Gemini
    "gemini": ("gemini", "gemini-1.5-pro"),
    "gemini-pro": ("gemini", "gemini-1.5-pro"),
    "gemini-flash": ("gemini", "gemini-1.5-flash"),
    "gemini-2": ("gemini", "gemini-2.0-flash-exp"),
}


def resolve_model(model: str) -> tuple[str, str]:
    """Resolve a model name to (provider, model_id).

    Args:
        model: Model name or alias.

    Returns:
        Tuple of (provider_name, model_id).

    Raises:
        ProviderError: If model cannot be resolved.
    """
    # Check if it's a known alias
    if model in MODEL_REGISTRY:
        return MODEL_REGISTRY[model]

    # Try to infer provider from model name
    if model.startswith("gpt-") or model.startswith("o1"):
        return ("openai", model)
    if model.startswith("claude-"):
        return ("anthropic", model)
    if model.startswith("gemini-"):
        return ("gemini", model)

    raise ProviderError(
        message=f"Unknown model: {model}. Use one of: {', '.join(sorted(MODEL_REGISTRY.keys()))}",
        provider="registry",
        code="config",
    )


def get_provider(model: str) -> Provider:
    """Get a provider instance for the given model.

    Args:
        model: Model name or alias.

    Returns:
        Configured provider instance.

    Raises:
        ProviderError: If model is unknown or provider cannot be initialized.
    """
    provider_name, model_id = resolve_model(model)

    if provider_name == "openai":
        from aicx.providers.openai import OpenAIProvider

        return OpenAIProvider(model_id=model_id)
    elif provider_name == "anthropic":
        from aicx.providers.anthropic import AnthropicProvider

        return AnthropicProvider(model_id=model_id)
    elif provider_name == "gemini":
        from aicx.providers.google import GeminiProvider

        return GeminiProvider(model_id=model_id)
    else:
        raise ProviderError(
            message=f"Unknown provider: {provider_name}",
            provider="registry",
            code="config",
        )


def list_models() -> list[str]:
    """List all available model aliases.

    Returns:
        Sorted list of model aliases.
    """
    return sorted(MODEL_REGISTRY.keys())
