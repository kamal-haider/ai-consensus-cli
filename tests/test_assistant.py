"""Tests for the interactive help assistant."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from aicx.assistant import (
    HELP_SYSTEM_PROMPT,
    _get_assistant_provider,
    _infer_provider,
    run_help_assistant,
)
from aicx.types import Response


class TestInferProvider:
    """Test provider inference from model ID."""

    def test_infer_openai_gpt(self):
        """Test inferring OpenAI from gpt- prefix."""
        assert _infer_provider("gpt-4o") == "openai"
        assert _infer_provider("gpt-4-turbo") == "openai"
        assert _infer_provider("GPT-3.5-turbo") == "openai"

    def test_infer_openai_o1(self):
        """Test inferring OpenAI from o1- prefix."""
        assert _infer_provider("o1-preview") == "openai"
        assert _infer_provider("o1-mini") == "openai"

    def test_infer_anthropic(self):
        """Test inferring Anthropic from claude- prefix."""
        assert _infer_provider("claude-3-opus") == "anthropic"
        assert _infer_provider("claude-sonnet-4") == "anthropic"
        assert _infer_provider("CLAUDE-3-5-sonnet") == "anthropic"

    def test_infer_gemini(self):
        """Test inferring Gemini from gemini- prefix."""
        assert _infer_provider("gemini-pro") == "gemini"
        assert _infer_provider("gemini-1.5-flash") == "gemini"
        assert _infer_provider("GEMINI-2.0") == "gemini"

    def test_infer_unknown(self):
        """Test unknown model returns None."""
        assert _infer_provider("unknown-model") is None
        assert _infer_provider("llama-3") is None


class TestGetAssistantProvider:
    """Test getting assistant provider."""

    def test_no_api_keys(self, monkeypatch):
        """Test returns None when no API keys set."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)

        result = _get_assistant_provider()
        assert result is None

    def test_prefers_anthropic(self, monkeypatch):
        """Test prefers Anthropic when available."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)

        result = _get_assistant_provider()
        assert result is not None
        assert result.provider == "anthropic"

    def test_falls_back_to_openai(self, monkeypatch):
        """Test falls back to OpenAI when Anthropic not available."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)

        result = _get_assistant_provider()
        assert result is not None
        assert result.provider == "openai"

    def test_uses_user_mediator(self, monkeypatch, tmp_path):
        """Test uses user's configured mediator when available."""
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)

        # Create user config with custom mediator
        config_dir = tmp_path / "aicx"
        config_dir.mkdir()
        config_file = config_dir / "config.toml"
        config_file.write_text('[defaults]\nmediator = "gpt-4-turbo"')

        result = _get_assistant_provider()
        assert result is not None
        assert result.model_id == "gpt-4-turbo"


class TestRunHelpAssistant:
    """Test running the help assistant."""

    def test_no_api_keys_returns_error(self, monkeypatch, capsys):
        """Test returns error when no API keys available."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)

        result = run_help_assistant("How do I use this?")
        assert result == 1

        captured = capsys.readouterr()
        assert "No API keys configured" in captured.out

    @patch("aicx.assistant.create_provider")
    def test_successful_response(self, mock_create, monkeypatch, capsys):
        """Test successful help response."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        mock_provider = MagicMock()
        mock_provider.create_chat_completion.return_value = Response(
            model_name="test",
            answer="Use --setup to configure defaults.",
        )
        mock_create.return_value = mock_provider

        result = run_help_assistant("How do I configure?")
        assert result == 0

        captured = capsys.readouterr()
        assert "Use --setup to configure defaults" in captured.out


class TestHelpSystemPrompt:
    """Test the help system prompt."""

    def test_prompt_contains_key_commands(self):
        """Test prompt mentions key CLI commands."""
        assert "--setup" in HELP_SYSTEM_PROMPT
        assert "--status" in HELP_SYSTEM_PROMPT
        assert "--models" in HELP_SYSTEM_PROMPT
        assert "--mediator" in HELP_SYSTEM_PROMPT

    def test_prompt_mentions_providers(self):
        """Test prompt mentions all providers."""
        assert "OpenAI" in HELP_SYSTEM_PROMPT
        assert "Anthropic" in HELP_SYSTEM_PROMPT
        assert "Google" in HELP_SYSTEM_PROMPT or "gemini" in HELP_SYSTEM_PROMPT

    def test_prompt_mentions_config_location(self):
        """Test prompt mentions config file location."""
        assert "~/.config/aicx" in HELP_SYSTEM_PROMPT
