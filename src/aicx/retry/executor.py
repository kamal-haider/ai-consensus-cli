"""Retry execution logic with exponential backoff."""

from __future__ import annotations

import random
import time
from typing import Callable, TypeVar

from aicx.logging import log_event
from aicx.retry.classifier import get_retry_after, is_retryable
from aicx.types import ProviderError, RetryConfig

T = TypeVar("T")


def calculate_delay(attempt: int, config: RetryConfig) -> float:
    """Calculate delay before next retry attempt.

    Uses exponential backoff: base_delay * (exponential_base ** attempt)
    Capped at max_delay_seconds.
    Optionally adds jitter (random 0-25% of delay).

    Args:
        attempt: The retry attempt number (0-indexed).
        config: Retry configuration.

    Returns:
        Number of seconds to delay before retrying.
    """
    # Calculate base exponential backoff
    delay = config.base_delay_seconds * (config.exponential_base**attempt)

    # Cap at maximum delay
    delay = min(delay, config.max_delay_seconds)

    # Add jitter if enabled
    if config.jitter:
        # Add random 0-25% of delay
        jitter_amount = delay * random.uniform(0, 0.25)
        delay += jitter_amount

    return delay


def execute_with_retry(
    fn: Callable[[], T],
    retry_config: RetryConfig,
    provider: str,
) -> T:
    """Execute a function with retry logic.

    Calls fn and retries on retryable ProviderError exceptions.
    Uses exponential backoff with optional jitter.

    Args:
        fn: The function to execute.
        retry_config: Retry configuration.
        provider: Provider name for logging.

    Returns:
        The result of fn().

    Raises:
        ProviderError: If fn fails with non-retryable error or max retries exceeded.
    """
    last_error: ProviderError | None = None
    total_attempts = retry_config.max_retries + 1

    for attempt in range(total_attempts):
        try:
            result = fn()
            if attempt > 0:
                log_event(
                    "retry_success",
                    model=provider,
                    payload={
                        "attempt": attempt,
                        "total_attempts": total_attempts,
                    },
                )
            return result
        except ProviderError as error:
            last_error = error

            # Check if error is retryable
            if not is_retryable(error):
                log_event(
                    "retry_not_retryable",
                    model=provider,
                    payload={
                        "error_code": error.code,
                        "message": str(error),
                    },
                )
                raise

            # Check if we have retries remaining
            if attempt >= retry_config.max_retries:
                log_event(
                    "retry_exhausted",
                    model=provider,
                    payload={
                        "attempt": attempt,
                        "total_attempts": total_attempts,
                        "error_code": error.code,
                        "message": str(error),
                    },
                )
                raise

            # Calculate delay with exponential backoff
            retry_after = get_retry_after(error)
            if retry_after is not None:
                delay = retry_after
            else:
                delay = calculate_delay(attempt, retry_config)

            log_event(
                "retry_attempt",
                model=provider,
                payload={
                    "attempt": attempt + 1,
                    "total_attempts": total_attempts,
                    "delay_seconds": delay,
                    "error_code": error.code,
                    "message": str(error),
                },
            )

            # Sleep before retrying
            time.sleep(delay)

    # Should never reach here, but satisfy type checker
    if last_error is not None:
        raise last_error
    raise RuntimeError("Unexpected state in retry logic")
