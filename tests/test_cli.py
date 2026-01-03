"""Tests for the CLI interface."""

import pytest
from unittest.mock import patch, Mock

from aicx.__main__ import main, build_parser


class TestParser:
    """Tests for argument parser."""

    def test_parser_has_query_command(self):
        """Parser includes query subcommand."""
        parser = build_parser()
        # Parse with query command
        args = parser.parse_args(["query", "test prompt"])
        assert args.command == "query"
        assert args.prompt == "test prompt"

    def test_parser_has_models_command(self):
        """Parser includes models subcommand."""
        parser = build_parser()
        args = parser.parse_args(["models"])
        assert args.command == "models"

    def test_query_default_model(self):
        """Query defaults to gpt-4o model."""
        parser = build_parser()
        args = parser.parse_args(["query", "test"])
        assert args.model == "gpt-4o"

    def test_query_custom_model(self):
        """Query accepts custom model."""
        parser = build_parser()
        args = parser.parse_args(["query", "test", "--model", "claude-sonnet"])
        assert args.model == "claude-sonnet"

    def test_query_short_model_flag(self):
        """Query accepts -m for model."""
        parser = build_parser()
        args = parser.parse_args(["query", "test", "-m", "gemini"])
        assert args.model == "gemini"

    def test_query_system_prompt(self):
        """Query accepts system prompt."""
        parser = build_parser()
        args = parser.parse_args(["query", "test", "--system", "Be helpful"])
        assert args.system == "Be helpful"

    def test_query_temperature(self):
        """Query accepts temperature."""
        parser = build_parser()
        args = parser.parse_args(["query", "test", "--temperature", "0.5"])
        assert args.temperature == 0.5

    def test_query_verbose(self):
        """Query accepts verbose flag."""
        parser = build_parser()
        args = parser.parse_args(["query", "test", "--verbose"])
        assert args.verbose is True

    def test_no_command_returns_none(self):
        """No command sets command to None."""
        parser = build_parser()
        args = parser.parse_args([])
        assert args.command is None


class TestMain:
    """Tests for main function."""

    def test_no_command_shows_help(self, capsys):
        """No command shows help and returns 0."""
        result = main([])
        assert result == 0
        captured = capsys.readouterr()
        assert "usage:" in captured.out.lower()

    def test_models_command(self, capsys):
        """Models command lists available models."""
        result = main(["models"])
        assert result == 0
        captured = capsys.readouterr()
        assert "Available models" in captured.out
        assert "gpt-4o" in captured.out

    @patch("aicx.__main__.get_provider")
    def test_query_success(self, mock_get_provider, capsys):
        """Query command returns model response."""
        mock_provider = Mock()
        mock_provider.query.return_value = "Hello from the model!"
        mock_get_provider.return_value = mock_provider

        result = main(["query", "Say hello"])
        assert result == 0
        captured = capsys.readouterr()
        assert "Hello from the model!" in captured.out

    @patch("aicx.__main__.get_provider")
    def test_query_verbose(self, mock_get_provider, capsys):
        """Query with verbose prints status."""
        mock_provider = Mock()
        mock_provider.query.return_value = "Response"
        mock_get_provider.return_value = mock_provider

        result = main(["query", "test", "--verbose"])
        assert result == 0
        captured = capsys.readouterr()
        assert "Querying" in captured.err

    @patch("aicx.__main__.get_provider")
    def test_query_auth_error(self, mock_get_provider, capsys):
        """Query returns 1 on auth error."""
        from aicx.providers import ProviderError
        mock_get_provider.side_effect = ProviderError(
            message="Missing API key",
            provider="openai",
            code="auth",
        )

        result = main(["query", "test"])
        assert result == 1
        captured = capsys.readouterr()
        assert "Error:" in captured.err

    @patch("aicx.__main__.get_provider")
    def test_query_provider_error(self, mock_get_provider, capsys):
        """Query returns 2 on provider error."""
        from aicx.providers import ProviderError
        mock_get_provider.side_effect = ProviderError(
            message="API error",
            provider="openai",
            code="api_error",
        )

        result = main(["query", "test"])
        assert result == 2
        captured = capsys.readouterr()
        assert "Error:" in captured.err
