"""Tests for mock provider adapter."""

from __future__ import annotations

import pytest

from aicx.models.mock import (
    MockProvider,
    create_approving_provider,
    create_echo_provider,
    create_mock_provider,
    create_objecting_provider,
)
from aicx.types import PromptRequest, ProviderError, Response, Role


@pytest.fixture
def basic_request() -> PromptRequest:
    """Create a basic prompt request for testing."""
    return PromptRequest(
        user_prompt="What is 2 + 2?",
        system_prompt="You are a helpful assistant.",
        round_index=0,
        role=Role.PARTICIPANT,
    )


@pytest.fixture
def round2_request() -> PromptRequest:
    """Create a round 2+ prompt request with candidate answer."""
    return PromptRequest(
        user_prompt="What is 2 + 2?",
        system_prompt="You are a helpful assistant.",
        round_index=1,
        role=Role.PARTICIPANT,
        candidate_answer="The answer is 4.",
    )


class TestMockProviderDefaults:
    """Tests for default MockProvider behavior."""

    def test_default_response_no_configuration(self, basic_request):
        """Test that default response is returned when no responses are configured."""
        provider = MockProvider()
        response = provider.create_chat_completion(basic_request)

        assert response.model_name == "mock"
        assert response.answer == "Mock response"
        assert response.approve is True
        assert response.critical is False

    def test_default_name(self):
        """Test that default name is 'mock'."""
        provider = MockProvider()
        assert provider.name == "mock"

    def test_custom_name(self):
        """Test that custom name is used."""
        provider = MockProvider(name="custom-mock")
        assert provider.name == "custom-mock"

    def test_supports_json_default(self):
        """Test that supports_json defaults to True."""
        provider = MockProvider()
        assert provider.supports_json is True

    def test_supports_json_custom(self):
        """Test that supports_json can be customized."""
        provider = MockProvider(supports_json=False)
        assert provider.supports_json is False


class TestConfiguredResponses:
    """Tests for pre-configured response sequences."""

    def test_single_configured_response(self, basic_request):
        """Test that single configured response is returned."""
        provider = MockProvider()
        responses = [
            Response(
                model_name="test",
                answer="Configured answer",
                approve=True,
                critical=False,
            )
        ]
        provider.configure_responses(responses)

        response = provider.create_chat_completion(basic_request)
        assert response.answer == "Configured answer"
        assert response.model_name == "test"

    def test_multiple_responses_cycle(self, basic_request):
        """Test that multiple responses cycle through the list."""
        provider = MockProvider()
        responses = [
            Response(model_name="test", answer="First", approve=True, critical=False),
            Response(model_name="test", answer="Second", approve=True, critical=False),
            Response(model_name="test", answer="Third", approve=True, critical=False),
        ]
        provider.configure_responses(responses)

        # First call
        response1 = provider.create_chat_completion(basic_request)
        assert response1.answer == "First"

        # Second call
        response2 = provider.create_chat_completion(basic_request)
        assert response2.answer == "Second"

        # Third call
        response3 = provider.create_chat_completion(basic_request)
        assert response3.answer == "Third"

        # Fourth call should cycle back to first
        response4 = provider.create_chat_completion(basic_request)
        assert response4.answer == "First"

    def test_response_cycling_continues(self, basic_request):
        """Test that response cycling continues for many calls."""
        provider = MockProvider()
        responses = [
            Response(model_name="test", answer="A", approve=True, critical=False),
            Response(model_name="test", answer="B", approve=True, critical=False),
        ]
        provider.configure_responses(responses)

        # Call 10 times and verify cycling
        for i in range(10):
            response = provider.create_chat_completion(basic_request)
            expected = "A" if i % 2 == 0 else "B"
            assert response.answer == expected

    def test_configure_responses_resets_index(self, basic_request):
        """Test that configuring responses resets the index."""
        provider = MockProvider()
        responses1 = [
            Response(model_name="test", answer="First", approve=True, critical=False),
            Response(model_name="test", answer="Second", approve=True, critical=False),
        ]
        provider.configure_responses(responses1)

        # Make a few calls
        provider.create_chat_completion(basic_request)
        provider.create_chat_completion(basic_request)

        # Reconfigure with new responses
        responses2 = [
            Response(model_name="test", answer="New", approve=True, critical=False),
        ]
        provider.configure_responses(responses2)

        # Should start from the beginning
        response = provider.create_chat_completion(basic_request)
        assert response.answer == "New"

    def test_configured_response_preserves_all_fields(self, basic_request):
        """Test that all response fields are preserved."""
        provider = MockProvider()
        responses = [
            Response(
                model_name="test-model",
                answer="Complete answer",
                approve=False,
                critical=True,
                objections=("Objection 1", "Objection 2"),
                missing=("Missing point",),
                edits=("Edit 1",),
                confidence=0.85,
                raw="Raw output",
            )
        ]
        provider.configure_responses(responses)

        response = provider.create_chat_completion(basic_request)
        assert response.model_name == "test-model"
        assert response.answer == "Complete answer"
        assert response.approve is False
        assert response.critical is True
        assert response.objections == ("Objection 1", "Objection 2")
        assert response.missing == ("Missing point",)
        assert response.edits == ("Edit 1",)
        assert response.confidence == 0.85
        assert response.raw == "Raw output"


class TestErrorSimulation:
    """Tests for error simulation on specific calls."""

    def test_error_on_first_call(self, basic_request):
        """Test that error is raised on first call when configured."""
        provider = MockProvider()
        provider.configure_error(on_call=0)

        with pytest.raises(ProviderError, match="Mock provider error"):
            provider.create_chat_completion(basic_request)

    def test_error_on_second_call(self, basic_request):
        """Test that error is raised on second call when configured."""
        provider = MockProvider()
        provider.configure_error(on_call=1)

        # First call should succeed
        response1 = provider.create_chat_completion(basic_request)
        assert response1.answer == "Mock response"

        # Second call should raise error
        with pytest.raises(ProviderError, match="Mock provider error"):
            provider.create_chat_completion(basic_request)

    def test_custom_error_raised(self, basic_request):
        """Test that custom error is raised when configured."""
        provider = MockProvider()
        custom_error = ValueError("Custom error message")
        provider.configure_error(on_call=0, error=custom_error)

        with pytest.raises(ValueError, match="Custom error message"):
            provider.create_chat_completion(basic_request)

    def test_error_with_provider_name(self, basic_request):
        """Test that default error includes provider name."""
        provider = MockProvider(name="test-provider")
        provider.configure_error(on_call=0)

        with pytest.raises(ProviderError) as exc_info:
            provider.create_chat_completion(basic_request)

        assert exc_info.value.provider == "test-provider"

    def test_error_only_on_specific_call(self, basic_request):
        """Test that error only occurs on the configured call."""
        provider = MockProvider()
        provider.configure_error(on_call=2)

        # First two calls should succeed
        provider.create_chat_completion(basic_request)
        provider.create_chat_completion(basic_request)

        # Third call should raise error
        with pytest.raises(ProviderError):
            provider.create_chat_completion(basic_request)

        # Subsequent calls should succeed again
        response = provider.create_chat_completion(basic_request)
        assert response.answer == "Mock response"

    def test_error_with_configured_responses(self, basic_request):
        """Test error simulation works with configured responses."""
        provider = MockProvider()
        responses = [
            Response(model_name="test", answer="First", approve=True, critical=False),
            Response(model_name="test", answer="Second", approve=True, critical=False),
        ]
        provider.configure_responses(responses)
        provider.configure_error(on_call=1)

        # First call should return configured response
        response1 = provider.create_chat_completion(basic_request)
        assert response1.answer == "First"

        # Second call should raise error
        with pytest.raises(ProviderError):
            provider.create_chat_completion(basic_request)


class TestDynamicResponseFunction:
    """Tests for dynamic response function."""

    def test_response_function_called(self, basic_request):
        """Test that response function is called."""
        provider = MockProvider()

        def custom_fn(request: PromptRequest) -> Response:
            return Response(
                model_name="custom",
                answer="Dynamic response",
                approve=True,
                critical=False,
            )

        provider.configure_response_fn(custom_fn)

        response = provider.create_chat_completion(basic_request)
        assert response.answer == "Dynamic response"
        assert response.model_name == "custom"

    def test_response_function_receives_request(self, basic_request):
        """Test that response function receives the prompt request."""
        provider = MockProvider()
        received_request = None

        def capture_fn(request: PromptRequest) -> Response:
            nonlocal received_request
            received_request = request
            return Response(
                model_name="test",
                answer="Response",
                approve=True,
                critical=False,
            )

        provider.configure_response_fn(capture_fn)
        provider.create_chat_completion(basic_request)

        assert received_request is not None
        assert received_request.user_prompt == "What is 2 + 2?"
        assert received_request.round_index == 0

    def test_response_function_can_access_request_fields(self):
        """Test that response function can use request fields in response."""
        provider = MockProvider()

        def dynamic_fn(request: PromptRequest) -> Response:
            return Response(
                model_name="dynamic",
                answer=f"User asked: {request.user_prompt}",
                approve=True,
                critical=False,
            )

        provider.configure_response_fn(dynamic_fn)

        request = PromptRequest(
            user_prompt="Test prompt",
            system_prompt="System",
            round_index=0,
            role=Role.PARTICIPANT,
        )
        response = provider.create_chat_completion(request)
        assert response.answer == "User asked: Test prompt"

    def test_response_function_overrides_configured_responses(self, basic_request):
        """Test that response function takes precedence over configured responses."""
        provider = MockProvider()

        # Configure both responses and function
        responses = [
            Response(model_name="test", answer="From list", approve=True, critical=False),
        ]
        provider.configure_responses(responses)

        def fn(request: PromptRequest) -> Response:
            return Response(
                model_name="test",
                answer="From function",
                approve=True,
                critical=False,
            )

        provider.configure_response_fn(fn)

        # Function should take precedence
        response = provider.create_chat_completion(basic_request)
        assert response.answer == "From function"

    def test_response_function_called_multiple_times(self, basic_request):
        """Test that response function is called for each request."""
        provider = MockProvider()
        call_count = 0

        def counting_fn(request: PromptRequest) -> Response:
            nonlocal call_count
            call_count += 1
            return Response(
                model_name="test",
                answer=f"Call {call_count}",
                approve=True,
                critical=False,
            )

        provider.configure_response_fn(counting_fn)

        response1 = provider.create_chat_completion(basic_request)
        response2 = provider.create_chat_completion(basic_request)
        response3 = provider.create_chat_completion(basic_request)

        assert response1.answer == "Call 1"
        assert response2.answer == "Call 2"
        assert response3.answer == "Call 3"
        assert call_count == 3


class TestProviderReset:
    """Tests for provider reset functionality."""

    def test_reset_clears_response_index(self, basic_request):
        """Test that reset clears the response index."""
        provider = MockProvider()
        responses = [
            Response(model_name="test", answer="First", approve=True, critical=False),
            Response(model_name="test", answer="Second", approve=True, critical=False),
        ]
        provider.configure_responses(responses)

        # Make a call to advance the index
        provider.create_chat_completion(basic_request)

        # Reset and verify we're back at the start
        provider.reset()
        response = provider.create_chat_completion(basic_request)
        assert response.answer == "First"

    def test_reset_clears_error_configuration(self, basic_request):
        """Test that reset clears error configuration."""
        provider = MockProvider()
        provider.configure_error(on_call=0)

        # Reset and verify error is not raised
        provider.reset()
        response = provider.create_chat_completion(basic_request)
        assert response.answer == "Mock response"

    def test_reset_clears_response_function(self, basic_request):
        """Test that reset clears response function."""
        provider = MockProvider()

        def fn(request: PromptRequest) -> Response:
            return Response(
                model_name="test",
                answer="From function",
                approve=True,
                critical=False,
            )

        provider.configure_response_fn(fn)

        # Reset and verify function is not used
        provider.reset()
        response = provider.create_chat_completion(basic_request)
        # Should fall back to default or configured responses
        assert response.answer != "From function"

    def test_reset_preserves_configured_responses(self, basic_request):
        """Test that reset preserves configured responses but resets index."""
        provider = MockProvider()
        responses = [
            Response(model_name="test", answer="First", approve=True, critical=False),
            Response(model_name="test", answer="Second", approve=True, critical=False),
        ]
        provider.configure_responses(responses)

        # Advance the index
        provider.create_chat_completion(basic_request)

        # Reset
        provider.reset()

        # Configured responses should still be there, but index reset
        response = provider.create_chat_completion(basic_request)
        assert response.answer == "First"

    def test_reset_can_be_called_multiple_times(self, basic_request):
        """Test that reset can be called multiple times safely."""
        provider = MockProvider()
        provider.configure_error(on_call=0)

        provider.reset()
        provider.reset()
        provider.reset()

        # Should work fine
        response = provider.create_chat_completion(basic_request)
        assert response.answer == "Mock response"


class TestCreateMockProvider:
    """Tests for create_mock_provider factory function."""

    def test_create_with_defaults(self):
        """Test creating mock provider with defaults."""
        provider = create_mock_provider()
        assert provider.name == "mock"
        assert provider.supports_json is True

    def test_create_with_custom_name(self):
        """Test creating mock provider with custom name."""
        provider = create_mock_provider(name="custom")
        assert provider.name == "custom"

    def test_create_with_supports_json_false(self):
        """Test creating mock provider with supports_json=False."""
        provider = create_mock_provider(supports_json=False)
        assert provider.supports_json is False

    def test_create_with_responses(self, basic_request):
        """Test creating mock provider with pre-configured responses."""
        responses = [
            Response(
                model_name="test",
                answer="Pre-configured",
                approve=True,
                critical=False,
            )
        ]
        provider = create_mock_provider(responses=responses)

        response = provider.create_chat_completion(basic_request)
        assert response.answer == "Pre-configured"

    def test_create_without_responses(self, basic_request):
        """Test creating mock provider without responses uses default."""
        provider = create_mock_provider()

        response = provider.create_chat_completion(basic_request)
        assert response.answer == "Mock response"

    def test_create_with_all_parameters(self, basic_request):
        """Test creating mock provider with all parameters."""
        responses = [
            Response(model_name="test", answer="Custom", approve=True, critical=False),
        ]
        provider = create_mock_provider(
            name="full-custom",
            responses=responses,
            supports_json=False,
        )

        assert provider.name == "full-custom"
        assert provider.supports_json is False
        response = provider.create_chat_completion(basic_request)
        assert response.answer == "Custom"


class TestCreateEchoProvider:
    """Tests for create_echo_provider factory function."""

    def test_echo_default_name(self):
        """Test that echo provider has default name 'echo'."""
        provider = create_echo_provider()
        assert provider.name == "echo"

    def test_echo_custom_name(self):
        """Test that echo provider can have custom name."""
        provider = create_echo_provider(name="custom-echo")
        assert provider.name == "custom-echo"

    def test_echo_returns_user_prompt(self):
        """Test that echo provider echoes the user prompt."""
        provider = create_echo_provider()
        request = PromptRequest(
            user_prompt="Hello world",
            system_prompt="System",
            round_index=0,
            role=Role.PARTICIPANT,
        )

        response = provider.create_chat_completion(request)
        assert response.answer == "Echo: Hello world"

    def test_echo_always_approves(self):
        """Test that echo provider always approves."""
        provider = create_echo_provider()
        request = PromptRequest(
            user_prompt="Test",
            system_prompt="System",
            round_index=1,
            role=Role.PARTICIPANT,
            candidate_answer="Some answer",
        )

        response = provider.create_chat_completion(request)
        assert response.approve is True
        assert response.critical is False

    def test_echo_preserves_model_name(self):
        """Test that echo provider uses the configured name in responses."""
        provider = create_echo_provider(name="my-echo")
        request = PromptRequest(
            user_prompt="Test",
            system_prompt="System",
            round_index=0,
            role=Role.PARTICIPANT,
        )

        response = provider.create_chat_completion(request)
        assert response.model_name == "my-echo"

    def test_echo_works_with_different_prompts(self):
        """Test that echo provider works with different prompts."""
        provider = create_echo_provider()

        prompts = [
            "First prompt",
            "Second prompt",
            "Third prompt with special chars: !@#$%",
        ]

        for prompt_text in prompts:
            request = PromptRequest(
                user_prompt=prompt_text,
                system_prompt="System",
                round_index=0,
                role=Role.PARTICIPANT,
            )
            response = provider.create_chat_completion(request)
            assert response.answer == f"Echo: {prompt_text}"


class TestCreateApprovingProvider:
    """Tests for create_approving_provider factory function."""

    def test_approving_default_name(self):
        """Test that approving provider has default name 'approver'."""
        provider = create_approving_provider()
        assert provider.name == "approver"

    def test_approving_custom_name(self):
        """Test that approving provider can have custom name."""
        provider = create_approving_provider(name="yes-man")
        assert provider.name == "yes-man"

    def test_approving_always_approves(self):
        """Test that approving provider always approves."""
        provider = create_approving_provider()
        request = PromptRequest(
            user_prompt="Test",
            system_prompt="System",
            round_index=1,
            role=Role.PARTICIPANT,
            candidate_answer="Some answer",
        )

        response = provider.create_chat_completion(request)
        assert response.approve is True
        assert response.critical is False

    def test_approving_has_approval_message(self):
        """Test that approving provider has an approval message."""
        provider = create_approving_provider()
        request = PromptRequest(
            user_prompt="Test",
            system_prompt="System",
            round_index=0,
            role=Role.PARTICIPANT,
        )

        response = provider.create_chat_completion(request)
        assert "approve" in response.answer.lower()

    def test_approving_preserves_model_name(self):
        """Test that approving provider uses the configured name in responses."""
        provider = create_approving_provider(name="always-yes")
        request = PromptRequest(
            user_prompt="Test",
            system_prompt="System",
            round_index=0,
            role=Role.PARTICIPANT,
        )

        response = provider.create_chat_completion(request)
        assert response.model_name == "always-yes"

    def test_approving_consistent_across_calls(self, basic_request):
        """Test that approving provider is consistent across multiple calls."""
        provider = create_approving_provider()

        for _ in range(5):
            response = provider.create_chat_completion(basic_request)
            assert response.approve is True
            assert response.critical is False


class TestCreateObjectingProvider:
    """Tests for create_objecting_provider factory function."""

    def test_objecting_default_name(self):
        """Test that objecting provider has default name 'objector'."""
        provider = create_objecting_provider()
        assert provider.name == "objector"

    def test_objecting_custom_name(self):
        """Test that objecting provider can have custom name."""
        provider = create_objecting_provider(name="critic")
        assert provider.name == "critic"

    def test_objecting_always_objects(self):
        """Test that objecting provider always objects critically."""
        provider = create_objecting_provider()
        request = PromptRequest(
            user_prompt="Test",
            system_prompt="System",
            round_index=1,
            role=Role.PARTICIPANT,
            candidate_answer="Some answer",
        )

        response = provider.create_chat_completion(request)
        assert response.approve is False
        assert response.critical is True

    def test_objecting_has_objections(self):
        """Test that objecting provider includes objections."""
        provider = create_objecting_provider()
        request = PromptRequest(
            user_prompt="Test",
            system_prompt="System",
            round_index=1,
            role=Role.PARTICIPANT,
            candidate_answer="Some answer",
        )

        response = provider.create_chat_completion(request)
        assert len(response.objections) > 0
        assert "incorrect" in response.objections[0].lower()

    def test_objecting_has_objection_message(self):
        """Test that objecting provider has an objection message."""
        provider = create_objecting_provider()
        request = PromptRequest(
            user_prompt="Test",
            system_prompt="System",
            round_index=0,
            role=Role.PARTICIPANT,
        )

        response = provider.create_chat_completion(request)
        assert "objection" in response.answer.lower()

    def test_objecting_preserves_model_name(self):
        """Test that objecting provider uses the configured name in responses."""
        provider = create_objecting_provider(name="always-no")
        request = PromptRequest(
            user_prompt="Test",
            system_prompt="System",
            round_index=0,
            role=Role.PARTICIPANT,
        )

        response = provider.create_chat_completion(request)
        assert response.model_name == "always-no"

    def test_objecting_consistent_across_calls(self, basic_request):
        """Test that objecting provider is consistent across multiple calls."""
        provider = create_objecting_provider()

        for _ in range(5):
            response = provider.create_chat_completion(basic_request)
            assert response.approve is False
            assert response.critical is True
            assert len(response.objections) > 0


class TestFactoryProviderInteraction:
    """Tests for interactions between different factory-created providers."""

    def test_different_provider_types_are_independent(self, basic_request):
        """Test that different provider types don't interfere with each other."""
        echo = create_echo_provider()
        approver = create_approving_provider()
        objector = create_objecting_provider()

        echo_response = echo.create_chat_completion(basic_request)
        approver_response = approver.create_chat_completion(basic_request)
        objector_response = objector.create_chat_completion(basic_request)

        # Each should maintain its own behavior
        assert "Echo:" in echo_response.answer
        assert approver_response.approve is True
        assert objector_response.approve is False

    def test_multiple_instances_are_independent(self, basic_request):
        """Test that multiple instances of the same type are independent."""
        echo1 = create_echo_provider(name="echo1")
        echo2 = create_echo_provider(name="echo2")

        response1 = echo1.create_chat_completion(basic_request)
        response2 = echo2.create_chat_completion(basic_request)

        assert response1.model_name == "echo1"
        assert response2.model_name == "echo2"


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_empty_user_prompt(self):
        """Test provider with empty user prompt."""
        provider = create_echo_provider()
        request = PromptRequest(
            user_prompt="",
            system_prompt="System",
            round_index=0,
            role=Role.PARTICIPANT,
        )

        response = provider.create_chat_completion(request)
        assert response.answer == "Echo: "

    def test_very_long_user_prompt(self):
        """Test provider with very long user prompt."""
        provider = create_echo_provider()
        long_prompt = "A" * 10000
        request = PromptRequest(
            user_prompt=long_prompt,
            system_prompt="System",
            round_index=0,
            role=Role.PARTICIPANT,
        )

        response = provider.create_chat_completion(request)
        assert response.answer == f"Echo: {long_prompt}"

    def test_special_characters_in_prompt(self):
        """Test provider with special characters in prompt."""
        provider = create_echo_provider()
        special_prompt = "Test with\nnewlines\tand\ttabs and \"quotes\""
        request = PromptRequest(
            user_prompt=special_prompt,
            system_prompt="System",
            round_index=0,
            role=Role.PARTICIPANT,
        )

        response = provider.create_chat_completion(request)
        assert response.answer == f"Echo: {special_prompt}"

    def test_unicode_in_prompt(self):
        """Test provider with unicode characters in prompt."""
        provider = create_echo_provider()
        unicode_prompt = "Hello 世界 🌍"
        request = PromptRequest(
            user_prompt=unicode_prompt,
            system_prompt="System",
            round_index=0,
            role=Role.PARTICIPANT,
        )

        response = provider.create_chat_completion(request)
        assert response.answer == f"Echo: {unicode_prompt}"

    def test_error_index_equal_to_call_count(self, basic_request):
        """Test error on exact call index."""
        provider = MockProvider()
        provider.configure_error(on_call=0)

        with pytest.raises(ProviderError):
            provider.create_chat_completion(basic_request)

    def test_error_index_beyond_expected_calls(self, basic_request):
        """Test error configured for call beyond expected usage."""
        provider = MockProvider()
        provider.configure_error(on_call=100)

        # Should work fine for many calls
        for _ in range(10):
            response = provider.create_chat_completion(basic_request)
            assert response.answer == "Mock response"
