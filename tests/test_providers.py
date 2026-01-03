"""Tests for the provider interface."""

import pytest
from unittest.mock import Mock, patch

from aicx.providers import ProviderError, get_provider, list_models
from aicx.providers.base import Provider
from aicx.providers.registry import resolve_model


class TestModelRegistry:
    """Tests for model alias resolution."""

    def test_resolve_known_alias(self):
        """Known aliases resolve to provider and model ID."""
        provider, model_id = resolve_model("gpt-4o")
        assert provider == "openai"
        assert model_id == "gpt-4o"

    def test_resolve_claude_alias(self):
        """Claude alias resolves correctly."""
        provider, model_id = resolve_model("claude-sonnet")
        assert provider == "anthropic"
        assert "claude" in model_id

    def test_resolve_gemini_alias(self):
        """Gemini alias resolves correctly."""
        provider, model_id = resolve_model("gemini")
        assert provider == "gemini"
        assert "gemini" in model_id

    def test_resolve_unknown_openai_model(self):
        """Unknown gpt- models infer OpenAI provider."""
        provider, model_id = resolve_model("gpt-5-turbo")
        assert provider == "openai"
        assert model_id == "gpt-5-turbo"

    def test_resolve_unknown_claude_model(self):
        """Unknown claude- models infer Anthropic provider."""
        provider, model_id = resolve_model("claude-4-opus")
        assert provider == "anthropic"
        assert model_id == "claude-4-opus"

    def test_resolve_unknown_gemini_model(self):
        """Unknown gemini- models infer Gemini provider."""
        provider, model_id = resolve_model("gemini-2.0-ultra")
        assert provider == "gemini"
        assert model_id == "gemini-2.0-ultra"

    def test_resolve_completely_unknown_model(self):
        """Completely unknown models raise ProviderError."""
        with pytest.raises(ProviderError) as exc_info:
            resolve_model("unknown-model")
        assert exc_info.value.code == "config"
        assert "Unknown model" in exc_info.value.message

    def test_list_models_returns_list(self):
        """list_models returns a sorted list of aliases."""
        models = list_models()
        assert isinstance(models, list)
        assert len(models) > 0
        assert models == sorted(models)


class TestGetProvider:
    """Tests for get_provider function."""

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_get_openai_provider(self):
        """get_provider returns OpenAI provider for gpt models."""
        provider = get_provider("gpt-4o")
        assert provider.name == "openai"
        assert hasattr(provider, "query")

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_get_anthropic_provider(self):
        """get_provider returns Anthropic provider for claude models."""
        provider = get_provider("claude-sonnet")
        assert provider.name == "anthropic"
        assert hasattr(provider, "query")

    @patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"})
    def test_get_gemini_provider(self):
        """get_provider returns Gemini provider for gemini models."""
        provider = get_provider("gemini")
        assert provider.name == "gemini"
        assert hasattr(provider, "query")

    @patch.dict("os.environ", {}, clear=True)
    def test_get_provider_missing_api_key(self):
        """get_provider raises ProviderError when API key is missing."""
        with pytest.raises(ProviderError) as exc_info:
            get_provider("gpt-4o")
        assert exc_info.value.code == "auth"


class TestOpenAIProvider:
    """Tests for OpenAI provider."""

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_init_with_api_key(self):
        """Provider initializes with API key."""
        from aicx.providers.openai import OpenAIProvider
        provider = OpenAIProvider()
        assert provider.name == "openai"
        assert provider.model_id == "gpt-4o"

    @patch.dict("os.environ", {}, clear=True)
    def test_init_without_api_key(self):
        """Provider raises error without API key."""
        from aicx.providers.openai import OpenAIProvider
        with pytest.raises(ProviderError) as exc_info:
            OpenAIProvider()
        assert exc_info.value.code == "auth"

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_query_calls_api(self):
        """query method calls the OpenAI API."""
        from aicx.providers.openai import OpenAIProvider

        provider = OpenAIProvider()

        # Mock the client
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Hello, world!"))]
        provider._client = Mock()
        provider._client.chat.completions.create.return_value = mock_response

        result = provider.query("Say hello")
        assert result == "Hello, world!"


class TestAnthropicProvider:
    """Tests for Anthropic provider."""

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_init_with_api_key(self):
        """Provider initializes with API key."""
        from aicx.providers.anthropic import AnthropicProvider
        provider = AnthropicProvider()
        assert provider.name == "anthropic"

    @patch.dict("os.environ", {}, clear=True)
    def test_init_without_api_key(self):
        """Provider raises error without API key."""
        from aicx.providers.anthropic import AnthropicProvider
        with pytest.raises(ProviderError) as exc_info:
            AnthropicProvider()
        assert exc_info.value.code == "auth"


class TestGeminiProvider:
    """Tests for Gemini provider."""

    @patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"})
    def test_init_with_api_key(self):
        """Provider initializes with API key."""
        from aicx.providers.google import GeminiProvider
        provider = GeminiProvider()
        assert provider.name == "gemini"

    @patch.dict("os.environ", {}, clear=True)
    def test_init_without_api_key(self):
        """Provider raises error without API key."""
        from aicx.providers.google import GeminiProvider
        with pytest.raises(ProviderError) as exc_info:
            GeminiProvider()
        assert exc_info.value.code == "auth"
