"""Error classification for retry policy."""

from __future__ import annotations

from aicx.types import ProviderError

# Error codes that should trigger a retry
RETRYABLE_CODES: frozenset[str] = frozenset(
    {
        "timeout",
        "network",
        "rate_limit",
        "service_unavailable",
    }
)

# Error codes that should not trigger a retry
NON_RETRYABLE_CODES: frozenset[str] = frozenset(
    {
        "auth",
        "config",
        "api_error",
    }
)


def is_retryable(error: ProviderError) -> bool:
    """Check if an error is retryable.

    Args:
        error: The provider error to check.

    Returns:
        True if the error should be retried, False otherwise.
    """
    if error.code is None:
        # If no code specified, treat as non-retryable
        return False

    return error.code in RETRYABLE_CODES


def get_retry_after(error: ProviderError) -> float | None:
    """Extract Retry-After header value if present.

    This is typically used for rate limit errors where the provider
    specifies how long to wait before retrying.

    Args:
        error: The provider error to check.

    Returns:
        Number of seconds to wait before retrying, or None if not specified.
    """
    # In v1, we don't have access to raw headers in ProviderError
    # This is a placeholder for future enhancement
    # For now, return None and rely on exponential backoff
    return None
