"""Tests for configuration loading and validation."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from aicx.config import load_config
from aicx.types import ConfigError, ShareMode


def test_default_config_when_no_file_exists():
    """Test that defaults are loaded when no config file exists."""
    config = load_config(config_path="/nonexistent/path/config.toml")

    assert len(config.models) == 2
    assert config.models[0].name == "gpt-4o"
    assert config.models[1].name == "claude-3-5"
    assert config.mediator.name == "gpt-4o"
    assert config.max_rounds == 3
    assert config.approval_ratio == 0.67
    assert config.change_threshold == 0.10
    assert config.share_mode == ShareMode.DIGEST
    assert config.verbose is False
    assert config.strict_json is False
    assert config.max_context_tokens is None


def test_load_valid_toml_config():
    """Test loading a valid TOML config file."""
    toml_content = """
[run]
max_rounds = 5
approval_ratio = 0.75
change_threshold = 0.15
share_mode = "raw"
max_context_tokens = 10000
strict_json = true
verbose = true

[[model]]
name = "model-a"
provider = "openai"
model_id = "gpt-4"
temperature = 0.3
max_tokens = 1024
timeout_seconds = 30
weight = 1.5

[[model]]
name = "model-b"
provider = "anthropic"
model_id = "claude-3"
temperature = 0.1
max_tokens = 512

[mediator]
name = "mediator-1"
provider = "openai"
model_id = "gpt-4o"
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        temp_path = f.name

    try:
        config = load_config(config_path=temp_path)

        assert len(config.models) == 2
        assert config.models[0].name == "model-a"
        assert config.models[0].temperature == 0.3
        assert config.models[0].max_tokens == 1024
        assert config.models[0].timeout_seconds == 30
        assert config.models[0].weight == 1.5
        assert config.models[1].name == "model-b"
        assert config.models[1].temperature == 0.1
        assert config.models[1].max_tokens == 512
        assert config.models[1].timeout_seconds == 60  # default

        assert config.mediator.name == "mediator-1"
        assert config.max_rounds == 5
        assert config.approval_ratio == 0.75
        assert config.change_threshold == 0.15
        assert config.share_mode == ShareMode.RAW
        assert config.max_context_tokens == 10000
        assert config.strict_json is True
        assert config.verbose is True
    finally:
        Path(temp_path).unlink()


def test_missing_required_model_field():
    """Test that missing required model fields raise ConfigError."""
    toml_content = """
[[model]]
name = "model-a"
provider = "openai"

[mediator]
name = "mediator-1"
provider = "openai"
model_id = "gpt-4o"
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        temp_path = f.name

    try:
        with pytest.raises(ConfigError, match="Missing required field: model_id"):
            load_config(config_path=temp_path)
    finally:
        Path(temp_path).unlink()


def test_duplicate_model_names():
    """Test that duplicate model names raise ConfigError."""
    toml_content = """
[[model]]
name = "duplicate"
provider = "openai"
model_id = "gpt-4"

[[model]]
name = "duplicate"
provider = "anthropic"
model_id = "claude-3"

[mediator]
name = "mediator-1"
provider = "openai"
model_id = "gpt-4o"
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        temp_path = f.name

    try:
        with pytest.raises(ConfigError, match="Duplicate model name: duplicate"):
            load_config(config_path=temp_path)
    finally:
        Path(temp_path).unlink()


def test_mediator_in_participant_list():
    """Test that mediator appearing in participant list raises ConfigError."""
    toml_content = """
[[model]]
name = "model-a"
provider = "openai"
model_id = "gpt-4"

[[model]]
name = "mediator-1"
provider = "openai"
model_id = "gpt-4o"

[mediator]
name = "mediator-1"
provider = "openai"
model_id = "gpt-4o"
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        temp_path = f.name

    try:
        with pytest.raises(ConfigError, match="must not appear in participant model list"):
            load_config(config_path=temp_path)
    finally:
        Path(temp_path).unlink()


def test_invalid_share_mode():
    """Test that invalid share_mode raises ConfigError."""
    toml_content = """
[run]
share_mode = "invalid"

[[model]]
name = "model-a"
provider = "openai"
model_id = "gpt-4"

[mediator]
name = "mediator-1"
provider = "openai"
model_id = "gpt-4o"
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        temp_path = f.name

    try:
        with pytest.raises(ConfigError, match="Invalid share_mode"):
            load_config(config_path=temp_path)
    finally:
        Path(temp_path).unlink()


def test_no_models_defined():
    """Test that config with no models raises ConfigError."""
    toml_content = """
[mediator]
name = "mediator-1"
provider = "openai"
model_id = "gpt-4o"
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        temp_path = f.name

    try:
        with pytest.raises(ConfigError, match="at least one"):
            load_config(config_path=temp_path)
    finally:
        Path(temp_path).unlink()


def test_no_mediator_defined():
    """Test that config with no mediator raises ConfigError."""
    toml_content = """
[[model]]
name = "model-a"
provider = "openai"
model_id = "gpt-4"
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        temp_path = f.name

    try:
        with pytest.raises(ConfigError, match="must define \\[mediator\\] section"):
            load_config(config_path=temp_path)
    finally:
        Path(temp_path).unlink()


def test_cli_override_models():
    """Test that --models flag overrides config file."""
    toml_content = """
[[model]]
name = "model-a"
provider = "openai"
model_id = "gpt-4"

[[model]]
name = "model-b"
provider = "anthropic"
model_id = "claude-3"

[[model]]
name = "model-c"
provider = "openai"
model_id = "gpt-3.5"

[mediator]
name = "mediator-1"
provider = "openai"
model_id = "gpt-4o"
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        temp_path = f.name

    try:
        config = load_config(config_path=temp_path, models="model-a,model-c")

        assert len(config.models) == 2
        assert config.models[0].name == "model-a"
        assert config.models[1].name == "model-c"
    finally:
        Path(temp_path).unlink()


def test_cli_override_mediator():
    """Test that --mediator flag overrides config file."""
    toml_content = """
[[model]]
name = "model-a"
provider = "openai"
model_id = "gpt-4"

[[model]]
name = "model-b"
provider = "anthropic"
model_id = "claude-3"

[mediator]
name = "original-mediator"
provider = "openai"
model_id = "gpt-4o"
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        temp_path = f.name

    try:
        # Use original-mediator as override (since it's defined in config)
        config = load_config(config_path=temp_path, mediator="original-mediator")
        assert config.mediator.name == "original-mediator"
    finally:
        Path(temp_path).unlink()


def test_cli_override_rounds():
    """Test that --rounds flag overrides config file."""
    config = load_config(config_path="/nonexistent/path/config.toml", rounds=7)
    assert config.max_rounds == 7


def test_cli_override_approval_ratio():
    """Test that --approval-ratio flag overrides config file."""
    config = load_config(config_path="/nonexistent/path/config.toml", approval_ratio=0.8)
    assert config.approval_ratio == 0.8


def test_cli_override_change_threshold():
    """Test that --change-threshold flag overrides config file."""
    config = load_config(config_path="/nonexistent/path/config.toml", change_threshold=0.05)
    assert config.change_threshold == 0.05


def test_cli_override_max_context_tokens():
    """Test that --max-context-tokens flag overrides config file."""
    config = load_config(config_path="/nonexistent/path/config.toml", max_context_tokens=8000)
    assert config.max_context_tokens == 8000


def test_cli_override_share_mode():
    """Test that --share-mode flag overrides config file."""
    config = load_config(config_path="/nonexistent/path/config.toml", share_mode="raw")
    assert config.share_mode == ShareMode.RAW


def test_cli_override_strict_json():
    """Test that --strict-json flag overrides config file."""
    config = load_config(config_path="/nonexistent/path/config.toml", strict_json=True)
    assert config.strict_json is True


def test_cli_override_verbose():
    """Test that --verbose flag overrides config file."""
    config = load_config(config_path="/nonexistent/path/config.toml", verbose=True)
    assert config.verbose is True


def test_invalid_model_name_in_override():
    """Test that invalid model name in override raises ConfigError."""
    with pytest.raises(ConfigError, match="Model 'nonexistent' not found"):
        load_config(config_path="/nonexistent/path/config.toml", models="nonexistent")


def test_invalid_mediator_name_in_override():
    """Test that invalid mediator name in override raises ConfigError."""
    with pytest.raises(ConfigError, match="Mediator 'nonexistent' not found"):
        load_config(config_path="/nonexistent/path/config.toml", mediator="nonexistent")


def test_mediator_as_participant_via_override():
    """Test that using mediator as participant via override raises ConfigError."""
    toml_content = """
[[model]]
name = "model-a"
provider = "openai"
model_id = "gpt-4"

[mediator]
name = "mediator-1"
provider = "openai"
model_id = "gpt-4o"
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        temp_path = f.name

    try:
        with pytest.raises(ConfigError, match="cannot also be a participant"):
            load_config(config_path=temp_path, models="mediator-1")
    finally:
        Path(temp_path).unlink()


def test_empty_models_override():
    """Test that empty --models flag raises ConfigError."""
    with pytest.raises(ConfigError, match="--models flag cannot be empty"):
        load_config(config_path="/nonexistent/path/config.toml", models="")


def test_invalid_share_mode_in_override():
    """Test that invalid --share-mode flag raises ConfigError."""
    with pytest.raises(ConfigError, match="Invalid --share-mode"):
        load_config(config_path="/nonexistent/path/config.toml", share_mode="invalid")


def test_model_config_validation():
    """Test that ModelConfig validates its values."""
    from aicx.types import ModelConfig

    # Valid model
    model = ModelConfig(
        name="test", provider="openai", model_id="gpt-4", temperature=0.5, weight=1.0
    )
    assert model.temperature == 0.5

    # Invalid temperature
    with pytest.raises(ValueError, match="temperature must be in"):
        ModelConfig(
            name="test", provider="openai", model_id="gpt-4", temperature=3.0
        )

    # Invalid weight
    with pytest.raises(ValueError, match="weight must be"):
        ModelConfig(name="test", provider="openai", model_id="gpt-4", weight=-1.0)

    # Invalid max_tokens
    with pytest.raises(ValueError, match="max_tokens must be"):
        ModelConfig(name="test", provider="openai", model_id="gpt-4", max_tokens=0)


def test_run_config_validation():
    """Test that RunConfig validates its values."""
    from aicx.types import ModelConfig, RunConfig

    model1 = ModelConfig(name="m1", provider="openai", model_id="gpt-4")
    model2 = ModelConfig(name="m2", provider="anthropic", model_id="claude-3")

    # Valid config
    config = RunConfig(models=(model1, model2), mediator=model1, max_rounds=3)
    assert config.max_rounds == 3

    # Not enough models
    with pytest.raises(ValueError, match="At least 2 models required"):
        RunConfig(models=(model1,), mediator=model1)

    # Invalid max_rounds
    with pytest.raises(ValueError, match="max_rounds must be"):
        RunConfig(models=(model1, model2), mediator=model1, max_rounds=0)

    # Invalid approval_ratio
    with pytest.raises(ValueError, match="approval_ratio must be"):
        RunConfig(models=(model1, model2), mediator=model1, approval_ratio=1.5)

    # Invalid change_threshold
    with pytest.raises(ValueError, match="change_threshold must be"):
        RunConfig(models=(model1, model2), mediator=model1, change_threshold=-0.1)

    # Invalid max_context_tokens
    with pytest.raises(ValueError, match="max_context_tokens must be"):
        RunConfig(models=(model1, model2), mediator=model1, max_context_tokens=0)
