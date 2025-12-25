"""Mock provider adapter for testing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from aicx.types import PromptRequest, ProviderError, Response


@dataclass
class MockProvider:
    """Mock provider adapter for testing.

    This provider returns configurable responses and can simulate errors.
    Useful for testing the consensus protocol without making real API calls.
    """

    name: str = "mock"
    supports_json: bool = True
    _responses: list[Response] = field(default_factory=list)
    _response_index: int = field(default=0, init=False)
    _error_on_call: int | None = None
    _error_to_raise: Exception | None = None
    _response_fn: Callable[[PromptRequest], Response] | None = None

    def create_chat_completion(self, request: PromptRequest) -> Response:
        """Return a pre-configured response or call response function.

        Args:
            request: The prompt request.

        Returns:
            A configured Response object.

        Raises:
            Exception: If configured to raise an error on this call.
        """
        # Capture current call index and increment for next call
        call_index = self._response_index
        self._response_index += 1

        # Check if we should raise an error on this call
        if self._error_on_call is not None and call_index == self._error_on_call:
            if self._error_to_raise is not None:
                raise self._error_to_raise
            raise ProviderError("Mock provider error", provider=self.name)

        # Use response function if provided
        if self._response_fn is not None:
            return self._response_fn(request)

        # Use pre-configured responses
        if not self._responses:
            # Default response if none configured
            return Response(
                model_name=self.name,
                answer="Mock response",
                approve=True,
                critical=False,
            )

        # Cycle through configured responses
        response = self._responses[call_index % len(self._responses)]
        return response

    def configure_responses(self, responses: list[Response]) -> None:
        """Configure the sequence of responses to return.

        Args:
            responses: List of Response objects to return in order (cycles).
        """
        self._responses = responses
        self._response_index = 0

    def configure_error(self, on_call: int, error: Exception | None = None) -> None:
        """Configure the provider to raise an error on a specific call.

        Args:
            on_call: The call index (0-based) on which to raise the error.
            error: The exception to raise (default: generic ProviderError).
        """
        self._error_on_call = on_call
        self._error_to_raise = error

    def configure_response_fn(
        self,
        fn: Callable[[PromptRequest], Response],
    ) -> None:
        """Configure a function to generate responses dynamically.

        Args:
            fn: Function that takes PromptRequest and returns Response.
        """
        self._response_fn = fn

    def reset(self) -> None:
        """Reset the provider state."""
        self._response_index = 0
        self._error_on_call = None
        self._error_to_raise = None
        self._response_fn = None


def create_mock_provider(
    name: str = "mock",
    responses: list[Response] | None = None,
    supports_json: bool = True,
) -> MockProvider:
    """Create a mock provider with optional pre-configured responses.

    Args:
        name: Provider name.
        responses: Optional list of responses to return in order.
        supports_json: Whether the provider supports JSON mode.

    Returns:
        A configured MockProvider instance.
    """
    provider = MockProvider(name=name, supports_json=supports_json)
    if responses:
        provider.configure_responses(responses)
    return provider


def create_echo_provider(name: str = "echo") -> MockProvider:
    """Create a mock provider that echoes the user prompt.

    Args:
        name: Provider name.

    Returns:
        A MockProvider that returns the user prompt as the answer.
    """
    provider = MockProvider(name=name)

    def echo_fn(request: PromptRequest) -> Response:
        return Response(
            model_name=name,
            answer=f"Echo: {request.user_prompt}",
            approve=True,
            critical=False,
        )

    provider.configure_response_fn(echo_fn)
    return provider


def create_approving_provider(name: str = "approver") -> MockProvider:
    """Create a mock provider that always approves.

    Args:
        name: Provider name.

    Returns:
        A MockProvider that always returns approve=True.
    """
    provider = MockProvider(name=name)

    def approve_fn(request: PromptRequest) -> Response:
        return Response(
            model_name=name,
            answer="I approve of the candidate answer.",
            approve=True,
            critical=False,
        )

    provider.configure_response_fn(approve_fn)
    return provider


def create_objecting_provider(name: str = "objector") -> MockProvider:
    """Create a mock provider that always objects critically.

    Args:
        name: Provider name.

    Returns:
        A MockProvider that always returns approve=False, critical=True.
    """
    provider = MockProvider(name=name)

    def object_fn(request: PromptRequest) -> Response:
        return Response(
            model_name=name,
            answer="I have critical objections.",
            approve=False,
            critical=True,
            objections=("This is incorrect.",),
        )

    provider.configure_response_fn(object_fn)
    return provider
