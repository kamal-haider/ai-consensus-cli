"""Provider error mapping utilities."""

from __future__ import annotations

import socket
from typing import Any

from aicx.types import ParseError, ProviderError


def map_network_error(exc: Exception, provider: str) -> ProviderError:
    """Map network-related exceptions to ProviderError.

    Args:
        exc: The original exception.
        provider: The provider name.

    Returns:
        ProviderError with appropriate code.
    """
    # Common network errors
    if isinstance(exc, socket.timeout):
        return ProviderError(
            f"Request to {provider} timed out: {exc}",
            provider=provider,
            code="timeout",
        )
    if isinstance(exc, (socket.gaierror, socket.error, ConnectionError)):
        return ProviderError(
            f"Network error connecting to {provider}: {exc}",
            provider=provider,
            code="network",
        )
    if isinstance(exc, TimeoutError):
        return ProviderError(
            f"Request to {provider} timed out: {exc}",
            provider=provider,
            code="timeout",
        )

    # Generic network error
    return ProviderError(
        f"Network error with {provider}: {exc}",
        provider=provider,
        code="network",
    )


def map_api_error(exc: Exception, provider: str) -> ProviderError:
    """Map provider API exceptions to ProviderError.

    Args:
        exc: The original exception (provider-specific API error).
        provider: The provider name.

    Returns:
        ProviderError with appropriate code.
    """
    error_str = str(exc)
    error_lower = error_str.lower()

    # Rate limiting
    if "rate limit" in error_lower or "429" in error_str:
        return ProviderError(
            f"Rate limit exceeded for {provider}: {exc}",
            provider=provider,
            code="rate_limit",
        )

    # Authentication
    if "auth" in error_lower or "401" in error_str or "403" in error_str:
        return ProviderError(
            f"Authentication error for {provider}: {exc}",
            provider=provider,
            code="auth",
        )

    # Timeout
    if "timeout" in error_lower or "timed out" in error_lower:
        return ProviderError(
            f"Request to {provider} timed out: {exc}",
            provider=provider,
            code="timeout",
        )

    # Service unavailable
    if "503" in error_str or "unavailable" in error_lower:
        return ProviderError(
            f"Service unavailable for {provider}: {exc}",
            provider=provider,
            code="service_unavailable",
        )

    # Generic API error
    return ProviderError(
        f"API error from {provider}: {exc}",
        provider=provider,
        code="api_error",
    )


def map_parse_error(output: str, reason: str) -> ParseError:
    """Map malformed output to ParseError.

    Args:
        output: The raw output from the model.
        reason: Description of what was malformed.

    Returns:
        ParseError with the raw output attached.
    """
    return ParseError(
        f"Failed to parse model output: {reason}",
        raw_output=output,
    )


def handle_provider_exception(
    exc: Exception,
    provider: str,
    context: str = "",
) -> ProviderError:
    """Handle any exception from a provider and map to ProviderError.

    This is a general handler that routes to specific mappers based on
    exception type.

    Args:
        exc: The exception raised.
        provider: The provider name.
        context: Optional context string for the error message.

    Returns:
        ProviderError with appropriate code.
    """
    # Already a ProviderError or ParseError
    if isinstance(exc, (ProviderError, ParseError)):
        return exc

    # Network errors
    if isinstance(
        exc,
        (socket.timeout, socket.error, ConnectionError, TimeoutError),
    ):
        return map_network_error(exc, provider)

    # Try to map as API error (for provider-specific exceptions)
    return map_api_error(exc, provider)
