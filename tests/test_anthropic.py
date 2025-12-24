"""Tests for Anthropic provider adapter."""

from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

import pytest
from anthropic import APIConnectionError, APITimeoutError, APIError

from aicx.models.anthropic import AnthropicProvider, create_anthropic_provider
from aicx.types import ModelConfig, ParseError, PromptRequest, ProviderError, Role


@pytest.fixture
def model_config():
    """Create a test model configuration."""
    return ModelConfig(
        name="claude-test",
        provider="anthropic",
        model_id="claude-3-5-sonnet-20241022",
        temperature=0.2,
        max_tokens=2048,
        timeout_seconds=60,
    )


@pytest.fixture
def prompt_request():
    """Create a test prompt request."""
    return PromptRequest(
        user_prompt="What is 2+2?",
        system_prompt="You are a helpful assistant.",
        round_index=0,
        role=Role.PARTICIPANT,
    )


def create_mock_response(content: str):
    """Create a mock Anthropic response."""
    mock_response = MagicMock()
    mock_content_block = MagicMock()
    mock_content_block.text = content
    mock_response.content = [mock_content_block]
    return mock_response


class TestAnthropicProviderCreation:
    """Tests for Anthropic provider creation."""

    def test_create_provider_success(self, model_config):
        """Test creating an Anthropic provider with valid API key."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            with patch("aicx.models.anthropic.Anthropic"):
                provider = create_anthropic_provider(model_config)
                assert provider.name == "anthropic"
                assert provider.supports_json is False
                assert provider.model_config == model_config

    def test_create_provider_missing_key(self, model_config):
        """Test creating an Anthropic provider without API key raises error."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            with pytest.raises(ProviderError) as exc_info:
                create_anthropic_provider(model_config)
            assert "ANTHROPIC_API_KEY" in str(exc_info.value)
            assert exc_info.value.code == "auth"


class TestAnthropicProviderCompletion:
    """Tests for Anthropic chat completion."""

    def test_successful_completion(self, model_config, prompt_request):
        """Test successful chat completion with JSON response."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            with patch("aicx.models.anthropic.Anthropic") as mock_anthropic:
                mock_client = MagicMock()
                mock_anthropic.return_value = mock_client

                provider = AnthropicProvider(model_config=model_config)

                json_response = {
                    "answer": "The answer is 4.",
                    "approve": True,
                    "critical": False,
                    "confidence": 0.95,
                }
                mock_response = create_mock_response(json.dumps(json_response))
                mock_client.messages.create.return_value = mock_response

                response = provider.create_chat_completion(prompt_request)

                assert response.model_name == "claude-test"
                assert response.answer == "The answer is 4."
                assert response.approve is True
                assert response.critical is False
                assert response.confidence == 0.95

    def test_completion_with_all_fields(self, model_config, prompt_request):
        """Test chat completion with all optional fields populated."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            with patch("aicx.models.anthropic.Anthropic") as mock_anthropic:
                mock_client = MagicMock()
                mock_anthropic.return_value = mock_client

                provider = AnthropicProvider(model_config=model_config)

                json_response = {
                    "answer": "The answer is 4.",
                    "approve": False,
                    "critical": True,
                    "objections": ["Wrong calculation", "Missing steps"],
                    "missing": ["Explanation"],
                    "edits": ["Add step-by-step"],
                    "confidence": 0.8,
                }
                mock_response = create_mock_response(json.dumps(json_response))
                mock_client.messages.create.return_value = mock_response

                response = provider.create_chat_completion(prompt_request)

                assert response.answer == "The answer is 4."
                assert response.approve is False
                assert response.critical is True
                assert response.objections == ("Wrong calculation", "Missing steps")
                assert response.missing == ("Explanation",)
                assert response.edits == ("Add step-by-step",)
                assert response.confidence == 0.8

    def test_api_call_parameters(self, model_config, prompt_request):
        """Test that API is called with correct parameters."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            with patch("aicx.models.anthropic.Anthropic") as mock_anthropic:
                mock_client = MagicMock()
                mock_anthropic.return_value = mock_client

                provider = AnthropicProvider(model_config=model_config)

                json_response = {"answer": "Test"}
                mock_response = create_mock_response(json.dumps(json_response))
                mock_client.messages.create.return_value = mock_response

                provider.create_chat_completion(prompt_request)

                call_kwargs = mock_client.messages.create.call_args.kwargs
                assert call_kwargs["model"] == "claude-3-5-sonnet-20241022"
                assert call_kwargs["system"] == "You are a helpful assistant."
                assert call_kwargs["messages"] == [{"role": "user", "content": "What is 2+2?"}]
                assert call_kwargs["temperature"] == 0.2
                assert call_kwargs["max_tokens"] == 2048
                assert call_kwargs["timeout"] == 60
                assert call_kwargs["top_p"] == 1.0


class TestAnthropicProviderErrors:
    """Tests for Anthropic error handling."""

    def test_timeout_error(self, model_config, prompt_request):
        """Test timeout error handling."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            with patch("aicx.models.anthropic.Anthropic") as mock_anthropic:
                mock_client = MagicMock()
                mock_anthropic.return_value = mock_client

                provider = AnthropicProvider(model_config=model_config)
                mock_client.messages.create.side_effect = APITimeoutError(
                    request=MagicMock()
                )

                with pytest.raises(ProviderError) as exc_info:
                    provider.create_chat_completion(prompt_request)
                assert exc_info.value.code == "timeout"

    def test_connection_error(self, model_config, prompt_request):
        """Test connection error handling."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            with patch("aicx.models.anthropic.Anthropic") as mock_anthropic:
                mock_client = MagicMock()
                mock_anthropic.return_value = mock_client

                provider = AnthropicProvider(model_config=model_config)
                mock_client.messages.create.side_effect = APIConnectionError(
                    request=MagicMock()
                )

                with pytest.raises(ProviderError) as exc_info:
                    provider.create_chat_completion(prompt_request)
                assert exc_info.value.provider == "anthropic"

    def test_api_error(self, model_config, prompt_request):
        """Test generic API error handling."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            with patch("aicx.models.anthropic.Anthropic") as mock_anthropic:
                mock_client = MagicMock()
                mock_anthropic.return_value = mock_client

                provider = AnthropicProvider(model_config=model_config)
                mock_client.messages.create.side_effect = APIError(
                    "429 Rate limit exceeded",
                    request=MagicMock(),
                    body=None,
                )

                with pytest.raises(ProviderError) as exc_info:
                    provider.create_chat_completion(prompt_request)
                assert exc_info.value.provider == "anthropic"


class TestAnthropicProviderParsing:
    """Tests for JSON parsing."""

    def test_invalid_json_response(self, model_config, prompt_request):
        """Test handling of invalid JSON in response."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            with patch("aicx.models.anthropic.Anthropic") as mock_anthropic:
                mock_client = MagicMock()
                mock_anthropic.return_value = mock_client

                provider = AnthropicProvider(model_config=model_config)
                mock_response = create_mock_response("This is not JSON")
                mock_client.messages.create.return_value = mock_response

                with pytest.raises(ParseError) as exc_info:
                    provider.create_chat_completion(prompt_request)
                assert "Invalid JSON" in str(exc_info.value)
                assert exc_info.value.raw_output == "This is not JSON"

    def test_empty_content(self, model_config, prompt_request):
        """Test handling of empty content response."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            with patch("aicx.models.anthropic.Anthropic") as mock_anthropic:
                mock_client = MagicMock()
                mock_anthropic.return_value = mock_client

                provider = AnthropicProvider(model_config=model_config)
                mock_response = MagicMock()
                mock_response.content = []
                mock_client.messages.create.return_value = mock_response

                with pytest.raises(ParseError) as exc_info:
                    provider.create_chat_completion(prompt_request)
                assert "Empty response" in str(exc_info.value)

    def test_missing_answer_returns_empty(self, model_config, prompt_request):
        """Test handling of JSON response missing 'answer' field."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            with patch("aicx.models.anthropic.Anthropic") as mock_anthropic:
                mock_client = MagicMock()
                mock_anthropic.return_value = mock_client

                provider = AnthropicProvider(model_config=model_config)
                json_response = {"approve": True, "critical": False}
                mock_response = create_mock_response(json.dumps(json_response))
                mock_client.messages.create.return_value = mock_response

                response = provider.create_chat_completion(prompt_request)
                assert response.answer == ""
