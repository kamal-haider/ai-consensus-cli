"""Tests for Gemini provider adapter."""

from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from aicx.models.gemini import GeminiProvider, create_gemini_provider
from aicx.types import ModelConfig, ParseError, PromptRequest, ProviderError, Role


@pytest.fixture
def model_config():
    """Create a test model configuration."""
    return ModelConfig(
        name="gemini-test",
        provider="gemini",
        model_id="gemini-1.5-pro",
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
    """Create a mock Gemini response."""
    mock_response = MagicMock()
    mock_response.text = content
    return mock_response


class TestGeminiProviderCreation:
    """Tests for Gemini provider creation."""

    def test_create_provider_success(self, model_config, monkeypatch):
        """Test creating a Gemini provider."""
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        with patch("google.genai.Client"):
            provider = create_gemini_provider(model_config)
            assert provider.name == "gemini"
            assert provider.supports_json is True
            assert provider.model_config == model_config

    def test_missing_api_key(self, model_config, monkeypatch):
        """Test that missing GEMINI_API_KEY raises ProviderError."""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

        with pytest.raises(ProviderError) as exc_info:
            GeminiProvider(model_config=model_config)
        assert exc_info.value.code == "auth"
        assert "GEMINI_API_KEY" in str(exc_info.value)

    def test_missing_model_config(self, prompt_request, monkeypatch):
        """Test that missing ModelConfig raises ProviderError."""
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")

        with patch("google.genai.Client"):
            provider = GeminiProvider()
            with pytest.raises(ProviderError) as exc_info:
                provider.create_chat_completion(prompt_request)
            assert exc_info.value.code == "config"


class TestGeminiProviderCompletion:
    """Tests for Gemini chat completion."""

    def test_successful_completion(self, model_config, prompt_request, monkeypatch):
        """Test successful chat completion with JSON response."""
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")

        json_response = {
            "answer": "The answer is 4.",
            "approve": True,
            "critical": False,
            "confidence": 0.95,
        }
        mock_response = create_mock_response(json.dumps(json_response))

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        with patch("google.genai.Client", return_value=mock_client):
            provider = GeminiProvider(model_config=model_config)
            response = provider.create_chat_completion(prompt_request)

        assert response.model_name == "gemini-test"
        assert response.answer == "The answer is 4."
        assert response.approve is True
        assert response.critical is False
        assert response.confidence == 0.95
        assert response.raw == json.dumps(json_response)

    def test_completion_with_all_fields(self, model_config, prompt_request, monkeypatch):
        """Test chat completion with all optional fields populated."""
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")

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

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        with patch("google.genai.Client", return_value=mock_client):
            provider = GeminiProvider(model_config=model_config)
            response = provider.create_chat_completion(prompt_request)

        assert response.answer == "The answer is 4."
        assert response.approve is False
        assert response.critical is True
        assert response.objections == ("Wrong calculation", "Missing steps")
        assert response.missing == ("Explanation",)
        assert response.edits == ("Add step-by-step",)
        assert response.confidence == 0.8

    def test_api_call_parameters(self, model_config, prompt_request, monkeypatch):
        """Test that API is called with correct parameters."""
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")

        mock_response = create_mock_response(json.dumps({"answer": "Test"}))

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        with patch("google.genai.Client", return_value=mock_client):
            provider = GeminiProvider(model_config=model_config)
            provider.create_chat_completion(prompt_request)

        call_kwargs = mock_client.models.generate_content.call_args.kwargs
        assert call_kwargs["model"] == "gemini-1.5-pro"
        assert call_kwargs["contents"] == "What is 2+2?"
        assert call_kwargs["config"].system_instruction == "You are a helpful assistant."
        assert call_kwargs["config"].temperature == 0.2
        assert call_kwargs["config"].max_output_tokens == 2048
        assert call_kwargs["config"].response_mime_type == "application/json"


class TestGeminiProviderErrors:
    """Tests for Gemini error handling."""

    def test_timeout_error(self, model_config, prompt_request, monkeypatch):
        """Test timeout error handling."""
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")

        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = TimeoutError("Request timed out")

        with patch("google.genai.Client", return_value=mock_client):
            provider = GeminiProvider(model_config=model_config)
            with pytest.raises(ProviderError) as exc_info:
                provider.create_chat_completion(prompt_request)
            assert exc_info.value.code == "timeout"

    def test_connection_error(self, model_config, prompt_request, monkeypatch):
        """Test connection error handling."""
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")

        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = ConnectionError("Connection failed")

        with patch("google.genai.Client", return_value=mock_client):
            provider = GeminiProvider(model_config=model_config)
            with pytest.raises(ProviderError) as exc_info:
                provider.create_chat_completion(prompt_request)
            assert exc_info.value.code == "network"

    def test_rate_limit_error(self, model_config, prompt_request, monkeypatch):
        """Test rate limit error handling."""
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")

        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("429 Rate limit exceeded")

        with patch("google.genai.Client", return_value=mock_client):
            provider = GeminiProvider(model_config=model_config)
            with pytest.raises(ProviderError) as exc_info:
                provider.create_chat_completion(prompt_request)
            assert exc_info.value.code == "rate_limit"


class TestGeminiProviderParsing:
    """Tests for JSON parsing."""

    def test_empty_response(self, model_config, prompt_request, monkeypatch):
        """Test that empty response raises ParseError."""
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")

        mock_response = MagicMock()
        mock_response.text = ""

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        with patch("google.genai.Client", return_value=mock_client):
            provider = GeminiProvider(model_config=model_config)
            with pytest.raises(ParseError) as exc_info:
                provider.create_chat_completion(prompt_request)
            assert "Empty response" in str(exc_info.value)

    def test_invalid_json(self, model_config, prompt_request, monkeypatch):
        """Test that invalid JSON raises ParseError."""
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")

        mock_response = create_mock_response("Not valid JSON {invalid}")

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        with patch("google.genai.Client", return_value=mock_client):
            provider = GeminiProvider(model_config=model_config)
            with pytest.raises(ParseError) as exc_info:
                provider.create_chat_completion(prompt_request)
            assert "Invalid JSON" in str(exc_info.value)
            assert exc_info.value.raw_output == "Not valid JSON {invalid}"

    def test_missing_answer_returns_empty(self, model_config, prompt_request, monkeypatch):
        """Test that missing answer field returns empty string."""
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")

        mock_response = create_mock_response(json.dumps({"confidence": 0.8}))

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        with patch("google.genai.Client", return_value=mock_client):
            provider = GeminiProvider(model_config=model_config)
            response = provider.create_chat_completion(prompt_request)

        assert response.answer == ""
        assert response.confidence == 0.8
