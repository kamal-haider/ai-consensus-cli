"""Model provider adapters."""

from aicx.models.errors import (
    handle_provider_exception,
    map_api_error,
    map_network_error,
    map_parse_error,
)
from aicx.models.mock import (
    MockProvider,
    create_approving_provider,
    create_echo_provider,
    create_mock_provider,
    create_objecting_provider,
)
from aicx.models.registry import (
    MODEL_ALIASES,
    ProviderAdapter,
    ProviderRegistry,
    default_registry,
)

__all__ = [
    # Registry
    "ProviderAdapter",
    "ProviderRegistry",
    "default_registry",
    "MODEL_ALIASES",
    # Mock providers
    "MockProvider",
    "create_mock_provider",
    "create_echo_provider",
    "create_approving_provider",
    "create_objecting_provider",
    # Error mapping
    "map_network_error",
    "map_api_error",
    "map_parse_error",
    "handle_provider_exception",
]
