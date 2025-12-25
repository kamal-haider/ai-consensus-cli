"""Tests for user configuration module."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from aicx.user_config import (
    DEFAULT_PROVIDER_MODELS,
    PROVIDER_SHORTHANDS,
    UserPreferences,
    check_api_key,
    expand_shorthand,
    get_api_key_status,
    get_user_config_dir,
    get_user_config_path,
    is_shorthand,
    load_user_preferences,
    save_user_preferences,
)


class TestUserConfigPaths:
    """Test user config path resolution."""

    def test_default_config_dir(self, monkeypatch):
        """Test default config dir is ~/.config/aicx."""
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
        config_dir = get_user_config_dir()
        assert config_dir == Path.home() / ".config" / "aicx"

    def test_xdg_config_home_override(self, monkeypatch):
        """Test XDG_CONFIG_HOME is respected."""
        monkeypatch.setenv("XDG_CONFIG_HOME", "/custom/config")
        config_dir = get_user_config_dir()
        assert config_dir == Path("/custom/config/aicx")

    def test_config_file_path(self, monkeypatch):
        """Test config file path."""
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
        config_path = get_user_config_path()
        assert config_path == Path.home() / ".config" / "aicx" / "config.toml"


class TestUserPreferences:
    """Test UserPreferences dataclass."""

    def test_empty_preferences(self):
        """Test creating empty preferences."""
        prefs = UserPreferences.empty()
        assert prefs.default_models == ()
        assert prefs.default_mediator is None
        assert prefs.shorthand_models == {}

    def test_preferences_with_values(self):
        """Test creating preferences with values."""
        prefs = UserPreferences(
            default_models=("gpt-4o", "claude-3-5"),
            default_mediator="gemini-pro",
            shorthand_models={"gpt": "gpt-4-turbo"},
        )
        assert prefs.default_models == ("gpt-4o", "claude-3-5")
        assert prefs.default_mediator == "gemini-pro"
        assert prefs.shorthand_models == {"gpt": "gpt-4-turbo"}


class TestLoadSavePreferences:
    """Test loading and saving preferences."""

    def test_load_nonexistent_file(self, monkeypatch):
        """Test loading from nonexistent file returns empty prefs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv("XDG_CONFIG_HOME", tmpdir)
            prefs = load_user_preferences()
            assert prefs == UserPreferences.empty()

    def test_save_and_load_preferences(self, monkeypatch):
        """Test saving and loading preferences."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv("XDG_CONFIG_HOME", tmpdir)

            prefs = UserPreferences(
                default_models=("gpt-4o", "claude-3-5"),
                default_mediator="gemini-pro",
                shorthand_models={"gpt": "gpt-4-turbo", "claude": "claude-opus"},
            )
            save_user_preferences(prefs)

            loaded = load_user_preferences()
            assert loaded.default_models == prefs.default_models
            assert loaded.default_mediator == prefs.default_mediator
            assert loaded.shorthand_models == prefs.shorthand_models

    def test_save_creates_directory(self, monkeypatch):
        """Test saving creates config directory if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_home = Path(tmpdir) / "nested" / "config"
            monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))

            prefs = UserPreferences(
                default_models=("gpt-4o",),
                default_mediator=None,
                shorthand_models={},
            )
            save_user_preferences(prefs)

            config_path = config_home / "aicx" / "config.toml"
            assert config_path.exists()

    def test_load_empty_models_list(self, monkeypatch):
        """Test loading config with no models returns empty tuple."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv("XDG_CONFIG_HOME", tmpdir)

            prefs = UserPreferences(
                default_models=(),
                default_mediator="gemini-pro",
                shorthand_models={},
            )
            save_user_preferences(prefs)

            loaded = load_user_preferences()
            assert loaded.default_models == ()


class TestApiKeyChecks:
    """Test API key checking functions."""

    def test_check_api_key_set(self, monkeypatch):
        """Test check_api_key returns True when key is set."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        assert check_api_key("openai") is True

    def test_check_api_key_not_set(self, monkeypatch):
        """Test check_api_key returns False when key is not set."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        assert check_api_key("openai") is False

    def test_check_api_key_unknown_provider(self):
        """Test check_api_key returns False for unknown provider."""
        assert check_api_key("unknown") is False

    def test_get_api_key_status(self, monkeypatch):
        """Test get_api_key_status returns dict of all providers."""
        monkeypatch.setenv("OPENAI_API_KEY", "test")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setenv("GEMINI_API_KEY", "test")

        status = get_api_key_status()
        assert status["openai"] is True
        assert status["anthropic"] is False
        assert status["gemini"] is True


class TestShorthandExpansion:
    """Test shorthand alias expansion."""

    def test_builtin_shorthands(self):
        """Test built-in shorthand expansion."""
        prefs = UserPreferences.empty()

        provider, model_id = expand_shorthand("gpt", prefs)
        assert provider == "openai"
        assert model_id == DEFAULT_PROVIDER_MODELS["openai"]

        provider, model_id = expand_shorthand("claude", prefs)
        assert provider == "anthropic"
        assert model_id == DEFAULT_PROVIDER_MODELS["anthropic"]

        provider, model_id = expand_shorthand("gemini", prefs)
        assert provider == "gemini"
        assert model_id == DEFAULT_PROVIDER_MODELS["gemini"]

    def test_user_shorthand_override(self):
        """Test user-defined shorthand overrides built-in."""
        prefs = UserPreferences(
            default_models=(),
            default_mediator=None,
            shorthand_models={"gpt": "gpt-4-turbo"},
        )

        provider, model_id = expand_shorthand("gpt", prefs)
        assert provider == "openai"
        assert model_id == "gpt-4-turbo"

    def test_non_shorthand_passthrough(self):
        """Test non-shorthand names pass through."""
        prefs = UserPreferences.empty()

        provider, model_id = expand_shorthand("custom-model", prefs)
        assert provider == ""
        assert model_id == "custom-model"

    def test_is_shorthand_builtin(self):
        """Test is_shorthand recognizes built-in shorthands."""
        assert is_shorthand("gpt") is True
        assert is_shorthand("claude") is True
        assert is_shorthand("gemini") is True
        assert is_shorthand("custom") is False

    def test_is_shorthand_user_defined(self):
        """Test is_shorthand recognizes user-defined shorthands."""
        prefs = UserPreferences(
            default_models=(),
            default_mediator=None,
            shorthand_models={"mymodel": "custom-id"},
        )
        assert is_shorthand("mymodel", prefs) is True
        assert is_shorthand("unknown", prefs) is False


class TestProviderConstants:
    """Test provider constants."""

    def test_provider_shorthands(self):
        """Test PROVIDER_SHORTHANDS contains expected mappings."""
        assert PROVIDER_SHORTHANDS["gpt"] == "openai"
        assert PROVIDER_SHORTHANDS["claude"] == "anthropic"
        assert PROVIDER_SHORTHANDS["gemini"] == "gemini"

    def test_default_provider_models(self):
        """Test DEFAULT_PROVIDER_MODELS contains expected defaults."""
        assert "openai" in DEFAULT_PROVIDER_MODELS
        assert "anthropic" in DEFAULT_PROVIDER_MODELS
        assert "gemini" in DEFAULT_PROVIDER_MODELS
