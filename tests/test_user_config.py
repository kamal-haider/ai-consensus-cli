"""Tests for user configuration module."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from aicx.user_config import (
    API_KEY_VARS,
    DEFAULT_PROVIDER_MODELS,
    PROVIDER_SHORTHANDS,
    UserPreferences,
    check_api_key,
    expand_shorthand,
    get_api_key_status,
    get_env_file_path,
    get_user_config_dir,
    get_user_config_path,
    is_shorthand,
    load_saved_api_keys,
    load_user_preferences,
    save_api_key,
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


class TestApiKeySaveLoad:
    """Test API key save/load functions."""

    def test_get_env_file_path(self, monkeypatch):
        """Test env file path resolution."""
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
        env_path = get_env_file_path()
        assert env_path == Path.home() / ".config" / "aicx" / ".env"

    def test_get_env_file_path_with_xdg(self, monkeypatch):
        """Test env file path with XDG_CONFIG_HOME."""
        monkeypatch.setenv("XDG_CONFIG_HOME", "/custom/config")
        env_path = get_env_file_path()
        assert env_path == Path("/custom/config/aicx/.env")

    def test_save_api_key(self, monkeypatch):
        """Test saving an API key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv("XDG_CONFIG_HOME", tmpdir)
            monkeypatch.delenv("OPENAI_API_KEY", raising=False)

            save_api_key("openai", "sk-test-key-12345")

            # Check file was created
            env_path = Path(tmpdir) / "aicx" / ".env"
            assert env_path.exists()

            # Check content
            content = env_path.read_text()
            assert 'OPENAI_API_KEY="sk-test-key-12345"' in content

            # Check env var was set
            assert os.environ.get("OPENAI_API_KEY") == "sk-test-key-12345"

    def test_save_multiple_api_keys(self, monkeypatch):
        """Test saving multiple API keys."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv("XDG_CONFIG_HOME", tmpdir)
            monkeypatch.delenv("OPENAI_API_KEY", raising=False)
            monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

            save_api_key("openai", "sk-openai-key")
            save_api_key("anthropic", "sk-anthropic-key")

            env_path = Path(tmpdir) / "aicx" / ".env"
            content = env_path.read_text()

            assert 'OPENAI_API_KEY="sk-openai-key"' in content
            assert 'ANTHROPIC_API_KEY="sk-anthropic-key"' in content

    def test_save_api_key_overwrites_existing(self, monkeypatch):
        """Test that saving an API key overwrites existing value."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv("XDG_CONFIG_HOME", tmpdir)
            monkeypatch.delenv("OPENAI_API_KEY", raising=False)

            save_api_key("openai", "old-key")
            save_api_key("openai", "new-key")

            env_path = Path(tmpdir) / "aicx" / ".env"
            content = env_path.read_text()

            assert "old-key" not in content
            assert 'OPENAI_API_KEY="new-key"' in content

    def test_load_saved_api_keys(self, monkeypatch):
        """Test loading saved API keys into environment."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv("XDG_CONFIG_HOME", tmpdir)
            monkeypatch.delenv("OPENAI_API_KEY", raising=False)
            monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

            # Create .env file
            env_dir = Path(tmpdir) / "aicx"
            env_dir.mkdir(parents=True)
            env_path = env_dir / ".env"
            env_path.write_text(
                '# API Keys\n'
                'OPENAI_API_KEY="sk-loaded-key"\n'
                'ANTHROPIC_API_KEY="sk-anthropic-loaded"\n'
            )

            load_saved_api_keys()

            assert os.environ.get("OPENAI_API_KEY") == "sk-loaded-key"
            assert os.environ.get("ANTHROPIC_API_KEY") == "sk-anthropic-loaded"

    def test_load_saved_api_keys_env_takes_precedence(self, monkeypatch):
        """Test that existing env vars are not overwritten."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv("XDG_CONFIG_HOME", tmpdir)
            monkeypatch.setenv("OPENAI_API_KEY", "env-key")

            # Create .env file with different value
            env_dir = Path(tmpdir) / "aicx"
            env_dir.mkdir(parents=True)
            env_path = env_dir / ".env"
            env_path.write_text('OPENAI_API_KEY="file-key"\n')

            load_saved_api_keys()

            # Env var should not be overwritten
            assert os.environ.get("OPENAI_API_KEY") == "env-key"

    def test_load_saved_api_keys_no_file(self, monkeypatch):
        """Test loading when no .env file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv("XDG_CONFIG_HOME", tmpdir)
            monkeypatch.delenv("OPENAI_API_KEY", raising=False)

            # Should not raise error
            load_saved_api_keys()

            assert os.environ.get("OPENAI_API_KEY") is None

    def test_load_saved_api_keys_handles_quotes(self, monkeypatch):
        """Test loading handles both single and double quotes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv("XDG_CONFIG_HOME", tmpdir)
            monkeypatch.delenv("OPENAI_API_KEY", raising=False)
            monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

            env_dir = Path(tmpdir) / "aicx"
            env_dir.mkdir(parents=True)
            env_path = env_dir / ".env"
            env_path.write_text(
                "OPENAI_API_KEY=\"double-quoted\"\n"
                "ANTHROPIC_API_KEY='single-quoted'\n"
            )

            load_saved_api_keys()

            assert os.environ.get("OPENAI_API_KEY") == "double-quoted"
            assert os.environ.get("ANTHROPIC_API_KEY") == "single-quoted"

    def test_load_saved_api_keys_skips_comments(self, monkeypatch):
        """Test that comments and empty lines are skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv("XDG_CONFIG_HOME", tmpdir)
            monkeypatch.delenv("OPENAI_API_KEY", raising=False)

            env_dir = Path(tmpdir) / "aicx"
            env_dir.mkdir(parents=True)
            env_path = env_dir / ".env"
            env_path.write_text(
                "# This is a comment\n"
                "\n"
                "OPENAI_API_KEY=valid-key\n"
                "# Another comment\n"
            )

            load_saved_api_keys()

            assert os.environ.get("OPENAI_API_KEY") == "valid-key"

    def test_api_key_vars_constant(self):
        """Test API_KEY_VARS contains all providers."""
        assert "openai" in API_KEY_VARS
        assert "anthropic" in API_KEY_VARS
        assert "gemini" in API_KEY_VARS
        assert API_KEY_VARS["openai"] == "OPENAI_API_KEY"
        assert API_KEY_VARS["anthropic"] == "ANTHROPIC_API_KEY"
        assert API_KEY_VARS["gemini"] == "GEMINI_API_KEY"
