"""Integration tests for the full consensus loop."""

from __future__ import annotations

import subprocess
import sys

import pytest

from aicx.__main__ import main, build_parser, VERSION
from aicx.config import load_config
from aicx.consensus.runner import run_consensus
from aicx.models.mock import (
    MockProvider,
    create_mock_provider,
    create_approving_provider,
    create_objecting_provider,
)
from aicx.types import ModelConfig, Response, RunConfig


# Fixtures


@pytest.fixture
def basic_config() -> RunConfig:
    """Create a basic config with 3 mock models."""
    return RunConfig(
        models=(
            ModelConfig(name="model-a", provider="mock", model_id="mock-1"),
            ModelConfig(name="model-b", provider="mock", model_id="mock-2"),
            ModelConfig(name="model-c", provider="mock", model_id="mock-3"),
        ),
        mediator=ModelConfig(name="mediator", provider="mock", model_id="mock-med"),
        max_rounds=3,
        approval_ratio=0.67,
    )


@pytest.fixture
def two_model_config() -> RunConfig:
    """Create a config with 2 models (minimum)."""
    return RunConfig(
        models=(
            ModelConfig(name="model-a", provider="mock", model_id="mock-1"),
            ModelConfig(name="model-b", provider="mock", model_id="mock-2"),
        ),
        mediator=ModelConfig(name="mediator", provider="mock", model_id="mock-med"),
        max_rounds=2,
        approval_ratio=0.5,
    )


# Integration tests: Full consensus loop


class TestConsensusHappyPath:
    """Test successful consensus scenarios."""

    def test_basic_consensus_completes(self, basic_config):
        """Test that a basic consensus run completes successfully."""
        result = run_consensus("What is 2 + 2?", basic_config)

        assert result is not None
        assert result.output is not None
        assert result.exit_code == 0
        assert result.rounds_completed >= 1

    def test_consensus_with_two_models(self, two_model_config):
        """Test consensus with minimum number of models."""
        result = run_consensus("Simple question", two_model_config)

        assert result is not None
        assert result.exit_code == 0

    def test_consensus_returns_mediator_state(self, basic_config):
        """Test that consensus result includes mediator state."""
        result = run_consensus("Test prompt", basic_config)

        assert result.mediator_state is not None
        assert result.mediator_state.candidate_answer is not None

    def test_consensus_tracks_rounds(self, basic_config):
        """Test that consensus tracks rounds completed."""
        result = run_consensus("Test prompt", basic_config)

        assert result.rounds_completed >= 1
        assert result.rounds_completed <= basic_config.max_rounds

    def test_consensus_includes_metadata(self, basic_config):
        """Test that consensus result includes metadata."""
        result = run_consensus("Test prompt", basic_config)

        assert "prompt" in result.metadata
        assert "participants" in result.metadata
        assert "quorum" in result.metadata
        assert result.metadata["prompt"] == "Test prompt"
        assert result.metadata["participants"] == 3


class TestConsensusWithOptions:
    """Test consensus with various configuration options."""

    def test_consensus_with_max_context_tokens(self, basic_config):
        """Test consensus with context budget."""
        config = RunConfig(
            models=basic_config.models,
            mediator=basic_config.mediator,
            max_rounds=3,
            max_context_tokens=10000,
        )

        result = run_consensus("Test with budget", config)

        assert result.exit_code == 0

    def test_consensus_with_low_approval_ratio(self, basic_config):
        """Test consensus with low approval threshold."""
        config = RunConfig(
            models=basic_config.models,
            mediator=basic_config.mediator,
            max_rounds=2,
            approval_ratio=0.34,  # Only need 1/3 approval
        )

        result = run_consensus("Easy consensus", config)

        assert result.exit_code == 0

    def test_consensus_no_summary_flag(self, basic_config):
        """Test that no_consensus_summary suppresses summary."""
        result = run_consensus(
            "Test prompt",
            basic_config,
            no_consensus_summary=True,
        )

        # Output should not contain disagreement summary markers
        assert "---" not in result.output or "Consensus:" not in result.output


# Integration tests: CLI parser


class TestCLIParser:
    """Test CLI argument parsing."""

    def test_parser_accepts_prompt(self):
        """Test that parser accepts a prompt."""
        parser = build_parser()
        args = parser.parse_args(["Test prompt"])

        assert args.prompt == "Test prompt"

    def test_parser_accepts_models_flag(self):
        """Test --models flag."""
        parser = build_parser()
        args = parser.parse_args(["prompt", "--models", "gpt-4o,claude-3"])

        assert args.models == "gpt-4o,claude-3"

    def test_parser_accepts_rounds_flag(self):
        """Test --rounds flag."""
        parser = build_parser()
        args = parser.parse_args(["prompt", "--rounds", "5"])

        assert args.rounds == 5

    def test_parser_accepts_approval_ratio_flag(self):
        """Test --approval-ratio flag."""
        parser = build_parser()
        args = parser.parse_args(["prompt", "--approval-ratio", "0.8"])

        assert args.approval_ratio == 0.8

    def test_parser_accepts_verbose_flag(self):
        """Test --verbose flag."""
        parser = build_parser()
        args = parser.parse_args(["prompt", "--verbose"])

        assert args.verbose is True

    def test_parser_accepts_strict_json_flag(self):
        """Test --strict-json flag."""
        parser = build_parser()
        args = parser.parse_args(["prompt", "--strict-json"])

        assert args.strict_json is True

    def test_parser_accepts_share_mode_flag(self):
        """Test --share-mode flag."""
        parser = build_parser()
        args = parser.parse_args(["prompt", "--share-mode", "raw"])

        assert args.share_mode == "raw"

    def test_parser_accepts_config_flag(self):
        """Test --config flag."""
        parser = build_parser()
        args = parser.parse_args(["prompt", "--config", "/path/to/config.toml"])

        assert args.config == "/path/to/config.toml"

    def test_parser_accepts_no_consensus_summary_flag(self):
        """Test --no-consensus-summary flag."""
        parser = build_parser()
        args = parser.parse_args(["prompt", "--no-consensus-summary"])

        assert args.no_consensus_summary is True


class TestCLIVersion:
    """Test CLI version flag."""

    def test_version_matches_pyproject(self):
        """Test that CLI version matches pyproject.toml."""
        assert VERSION == "0.1.0"


# Integration tests: Config loading


class TestConfigIntegration:
    """Test config loading integration."""

    def test_load_default_config(self):
        """Test loading default config when file doesn't exist."""
        config = load_config("/nonexistent/path.toml")

        assert config is not None
        assert len(config.models) >= 2
        assert config.mediator is not None

    def test_config_override_rounds(self):
        """Test overriding rounds via CLI."""
        config = load_config("/nonexistent/path.toml", rounds=5)

        assert config.max_rounds == 5

    def test_config_override_approval_ratio(self):
        """Test overriding approval_ratio via CLI."""
        config = load_config("/nonexistent/path.toml", approval_ratio=0.8)

        assert config.approval_ratio == 0.8

    def test_config_override_verbose(self):
        """Test overriding verbose via CLI."""
        config = load_config("/nonexistent/path.toml", verbose=True)

        assert config.verbose is True


# Integration tests: Mock providers


class TestMockProviderIntegration:
    """Test mock provider integration."""

    def test_mock_provider_returns_response(self):
        """Test that mock provider returns a valid response."""
        provider = create_mock_provider("test-mock")

        from aicx.types import PromptRequest, Role

        request = PromptRequest(
            user_prompt="Test question",
            system_prompt="You are helpful",
            round_index=0,
            role=Role.PARTICIPANT,
        )

        response = provider.create_chat_completion(request)

        assert response is not None
        assert response.model_name == "test-mock"

    def test_approving_provider_approves(self):
        """Test that approving provider always approves."""
        provider = create_approving_provider("approver")

        from aicx.types import PromptRequest, Role

        request = PromptRequest(
            user_prompt="Test",
            system_prompt="System",
            round_index=1,
            role=Role.PARTICIPANT,
        )

        response = provider.create_chat_completion(request)

        assert response.approve is True
        assert response.critical is False

    def test_objecting_provider_objects(self):
        """Test that objecting provider always objects."""
        provider = create_objecting_provider("objector")

        from aicx.types import PromptRequest, Role

        request = PromptRequest(
            user_prompt="Test",
            system_prompt="System",
            round_index=1,
            role=Role.PARTICIPANT,
        )

        response = provider.create_chat_completion(request)

        assert response.approve is False
        assert response.critical is True
        assert len(response.objections) > 0


# End-to-end tests


class TestEndToEnd:
    """End-to-end tests using subprocess."""

    def test_cli_help(self):
        """Test that CLI help works."""
        result = subprocess.run(
            [sys.executable, "-m", "aicx", "--help"],
            capture_output=True,
            text=True,
            cwd="/Users/manik/Programs/python/ai-consensus-cli",
            env={"PYTHONPATH": "src"},
        )

        assert result.returncode == 0
        assert "AI Consensus CLI" in result.stdout
        assert "--models" in result.stdout
        assert "--rounds" in result.stdout

    def test_cli_version(self):
        """Test that CLI version works."""
        result = subprocess.run(
            [sys.executable, "-m", "aicx", "--version"],
            capture_output=True,
            text=True,
            cwd="/Users/manik/Programs/python/ai-consensus-cli",
            env={"PYTHONPATH": "src"},
        )

        assert result.returncode == 0
        assert "0.1.0" in result.stdout
