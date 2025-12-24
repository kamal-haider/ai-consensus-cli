"""Provider wrapper with retry logic."""

from __future__ import annotations

from aicx.models.registry import ProviderAdapter
from aicx.retry.executor import execute_with_retry
from aicx.types import PromptRequest, Response, RetryConfig


class RetryableProvider:
    """Wrapper that adds retry logic to a ProviderAdapter.

    This class wraps any ProviderAdapter and applies retry logic to
    the create_chat_completion method. All other attributes are passed
    through to the wrapped adapter.
    """

    def __init__(self, adapter: ProviderAdapter, retry_config: RetryConfig):
        """Initialize the retryable provider wrapper.

        Args:
            adapter: The provider adapter to wrap.
            retry_config: Retry configuration to apply.
        """
        self._adapter = adapter
        self._retry_config = retry_config

    @property
    def name(self) -> str:
        """Get the provider name from the wrapped adapter."""
        return self._adapter.name

    @property
    def supports_json(self) -> bool:
        """Get JSON support from the wrapped adapter."""
        return self._adapter.supports_json

    def create_chat_completion(self, request: PromptRequest) -> Response:
        """Send a chat completion request with retry logic.

        Args:
            request: The prompt request containing user prompt, system prompt, etc.

        Returns:
            Response object with model output.

        Raises:
            ProviderError: On network/timeout/API errors after retries exhausted.
            ParseError: On malformed model output.
        """

        def call_adapter() -> Response:
            return self._adapter.create_chat_completion(request)

        return execute_with_retry(
            fn=call_adapter,
            retry_config=self._retry_config,
            provider=self.name,
        )


def wrap_with_retry(
    adapter: ProviderAdapter, retry_config: RetryConfig | None
) -> ProviderAdapter:
    """Wrap a provider adapter with retry logic if configured.

    Args:
        adapter: The provider adapter to wrap.
        retry_config: Retry configuration, or None to use adapter as-is.

    Returns:
        The wrapped provider adapter if retry_config is provided,
        otherwise the original adapter unchanged.
    """
    if retry_config is None:
        return adapter
    return RetryableProvider(adapter, retry_config)
