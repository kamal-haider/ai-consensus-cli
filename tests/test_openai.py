"""Tests for OpenAI provider adapter."""

from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

import pytest
from openai import APIConnectionError, APITimeoutError, RateLimitError
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice

from aicx.models.openai import OpenAIProvider, create_openai_provider
from aicx.types import ModelConfig, ParseError, PromptRequest, ProviderError, Role


@pytest.fixture
def model_config():
    """Create a test model configuration."""
    return ModelConfig(
        name="test-gpt",
        provider="openai",
        model_id="gpt-4o",
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


def create_mock_completion(content: str) -> ChatCompletion:
    """Create a mock ChatCompletion object."""
    return ChatCompletion(
        id="test-id",
        choices=[
            Choice(
                finish_reason="stop",
                index=0,
                message=ChatCompletionMessage(
                    content=content,
                    role="assistant",
                ),
            )
        ],
        created=1234567890,
        model="gpt-4o",
        object="chat.completion",
    )


class TestOpenAIProviderCreation:
    """Tests for OpenAI provider creation."""

    def test_create_provider_success(self, model_config):
        """Test creating an OpenAI provider with valid API key."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("aicx.models.openai.OpenAI"):
                provider = create_openai_provider(model_config)
                assert provider.name == "openai"
                assert provider.supports_json is True
                assert provider.model_config == model_config

    def test_create_provider_missing_key(self, model_config):
        """Test creating an OpenAI provider without API key raises error."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove OPENAI_API_KEY if it exists
            os.environ.pop("OPENAI_API_KEY", None)
            with pytest.raises(ProviderError) as exc_info:
                create_openai_provider(model_config)
            assert "OPENAI_API_KEY" in str(exc_info.value)
            assert exc_info.value.code == "auth"


class TestOpenAIProviderCompletion:
    """Tests for OpenAI chat completion."""

    def test_successful_completion(self, model_config, prompt_request):
        """Test successful chat completion with JSON response."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("aicx.models.openai.OpenAI") as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client

                provider = OpenAIProvider(model_config=model_config)

                json_response = {
                    "answer": "The answer is 4.",
                    "approve": True,
                    "critical": False,
                    "confidence": 0.95,
                }
                mock_completion = create_mock_completion(json.dumps(json_response))
                mock_client.chat.completions.create.return_value = mock_completion

                response = provider.create_chat_completion(prompt_request)

                assert response.model_name == "test-gpt"
                assert response.answer == "The answer is 4."
                assert response.approve is True
                assert response.critical is False
                assert response.confidence == 0.95
                assert response.raw == json.dumps(json_response)

    def test_completion_with_all_fields(self, model_config, prompt_request):
        """Test chat completion with all optional fields populated."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("aicx.models.openai.OpenAI") as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client

                provider = OpenAIProvider(model_config=model_config)

                json_response = {
                    "answer": "The answer is 4.",
                    "approve": False,
                    "critical": True,
                    "objections": ["Wrong calculation", "Missing steps"],
                    "missing": ["Explanation"],
                    "edits": ["Add step-by-step"],
                    "confidence": 0.8,
                }
                mock_completion = create_mock_completion(json.dumps(json_response))
                mock_client.chat.completions.create.return_value = mock_completion

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
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("aicx.models.openai.OpenAI") as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client

                provider = OpenAIProvider(model_config=model_config)

                json_response = {"answer": "Test"}
                mock_completion = create_mock_completion(json.dumps(json_response))
                mock_client.chat.completions.create.return_value = mock_completion

                provider.create_chat_completion(prompt_request)

                call_kwargs = mock_client.chat.completions.create.call_args.kwargs
                assert call_kwargs["model"] == "gpt-4o"
                assert call_kwargs["temperature"] == 0.2
                assert call_kwargs["max_tokens"] == 2048
                assert call_kwargs["timeout"] == 60
                assert call_kwargs["top_p"] == 1.0
                assert call_kwargs["response_format"] == {"type": "json_object"}


class TestOpenAIProviderErrors:
    """Tests for OpenAI error handling."""

    def test_timeout_error(self, model_config, prompt_request):
        """Test timeout error handling."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("aicx.models.openai.OpenAI") as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client

                provider = OpenAIProvider(model_config=model_config)
                mock_client.chat.completions.create.side_effect = APITimeoutError(
                    "Request timed out"
                )

                with pytest.raises(ProviderError) as exc_info:
                    provider.create_chat_completion(prompt_request)
                assert exc_info.value.code == "timeout"
                assert "timed out" in str(exc_info.value).lower()

    def test_connection_error(self, model_config, prompt_request):
        """Test connection error handling."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("aicx.models.openai.OpenAI") as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client

                provider = OpenAIProvider(model_config=model_config)
                mock_client.chat.completions.create.side_effect = APIConnectionError(
                    request=MagicMock()
                )

                with pytest.raises(ProviderError) as exc_info:
                    provider.create_chat_completion(prompt_request)
                assert exc_info.value.code == "network"

    def test_rate_limit_error(self, model_config, prompt_request):
        """Test rate limit error handling."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("aicx.models.openai.OpenAI") as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client

                provider = OpenAIProvider(model_config=model_config)
                mock_client.chat.completions.create.side_effect = RateLimitError(
                    "Rate limit exceeded",
                    response=MagicMock(),
                    body=None,
                )

                with pytest.raises(ProviderError) as exc_info:
                    provider.create_chat_completion(prompt_request)
                assert exc_info.value.code == "rate_limit"


class TestOpenAIProviderParsing:
    """Tests for JSON parsing."""

    def test_invalid_json_response(self, model_config, prompt_request):
        """Test handling of invalid JSON in response."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("aicx.models.openai.OpenAI") as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client

                provider = OpenAIProvider(model_config=model_config)
                mock_completion = create_mock_completion("This is not JSON")
                mock_client.chat.completions.create.return_value = mock_completion

                with pytest.raises(ParseError) as exc_info:
                    provider.create_chat_completion(prompt_request)
                assert "Invalid JSON" in str(exc_info.value)
                assert exc_info.value.raw_output == "This is not JSON"

    def test_empty_choices(self, model_config, prompt_request):
        """Test handling of completion response with no choices."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("aicx.models.openai.OpenAI") as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client

                provider = OpenAIProvider(model_config=model_config)
                mock_completion = ChatCompletion(
                    id="test-id",
                    choices=[],
                    created=1234567890,
                    model="gpt-4o",
                    object="chat.completion",
                )
                mock_client.chat.completions.create.return_value = mock_completion

                with pytest.raises(ParseError) as exc_info:
                    provider.create_chat_completion(prompt_request)
                assert "No choices" in str(exc_info.value)

    def test_null_content(self, model_config, prompt_request):
        """Test handling of completion response with null content."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("aicx.models.openai.OpenAI") as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client

                provider = OpenAIProvider(model_config=model_config)
                mock_completion = ChatCompletion(
                    id="test-id",
                    choices=[
                        Choice(
                            finish_reason="stop",
                            index=0,
                            message=ChatCompletionMessage(
                                content=None,
                                role="assistant",
                            ),
                        )
                    ],
                    created=1234567890,
                    model="gpt-4o",
                    object="chat.completion",
                )
                mock_client.chat.completions.create.return_value = mock_completion

                with pytest.raises(ParseError) as exc_info:
                    provider.create_chat_completion(prompt_request)
                assert "Empty content" in str(exc_info.value)

    def test_missing_answer_returns_empty(self, model_config, prompt_request):
        """Test handling of JSON response missing 'answer' field."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("aicx.models.openai.OpenAI") as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client

                provider = OpenAIProvider(model_config=model_config)
                json_response = {"approve": True, "critical": False}
                mock_completion = create_mock_completion(json.dumps(json_response))
                mock_client.chat.completions.create.return_value = mock_completion

                response = provider.create_chat_completion(prompt_request)
                assert response.answer == ""
