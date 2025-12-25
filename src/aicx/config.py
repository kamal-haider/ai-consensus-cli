"""Configuration loading and validation."""

from __future__ import annotations

import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aicx.types import ConfigError, ModelConfig, RunConfig, ShareMode
from aicx.user_config import (
    DEFAULT_PROVIDER_MODELS,
    PROVIDER_SHORTHANDS,
    UserPreferences,
    expand_shorthand,
    is_shorthand,
    load_user_preferences,
)


DEFAULT_CONFIG_PATH = Path("config/config.toml")


@dataclass(frozen=True)
class ConfigOverrides:
    """CLI flag overrides for config values."""

    models: str | None
    mediator: str | None
    rounds: int | None
    approval_ratio: float | None
    change_threshold: float | None
    max_context_tokens: int | None
    share_mode: str | None
    strict_json: bool | None
    verbose: bool | None


def load_config(
    config_path: str | None,
    *,
    models: str | None = None,
    mediator: str | None = None,
    rounds: int | None = None,
    approval_ratio: float | None = None,
    change_threshold: float | None = None,
    max_context_tokens: int | None = None,
    share_mode: str | None = None,
    strict_json: bool | None = None,
    verbose: bool | None = None,
) -> RunConfig:
    """Load and validate configuration from file and CLI overrides.

    Fallback chain: CLI flags -> user config -> project config -> built-in defaults

    Args:
        config_path: Path to TOML config file, or None to use default.
        models: Comma-separated model names to use (overrides config).
        mediator: Mediator model name (overrides config).
        rounds: Max rounds (overrides config).
        approval_ratio: Approval ratio (overrides config).
        change_threshold: Change threshold (overrides config).
        max_context_tokens: Max context tokens (overrides config).
        share_mode: Share mode (overrides config).
        strict_json: Strict JSON mode (overrides config).
        verbose: Verbose mode (overrides config).

    Returns:
        Validated RunConfig.

    Raises:
        ConfigError: If config is invalid or missing required values.
    """
    overrides = ConfigOverrides(
        models=models,
        mediator=mediator,
        rounds=rounds,
        approval_ratio=approval_ratio,
        change_threshold=change_threshold,
        max_context_tokens=max_context_tokens,
        share_mode=share_mode,
        strict_json=strict_json,
        verbose=verbose,
    )

    # Load user preferences
    user_prefs = load_user_preferences()

    # Load base config from file or defaults
    base_config = _load_from_file(config_path)

    # Apply user preferences, then CLI overrides
    return _apply_overrides(base_config, overrides, user_prefs)


def _load_from_file(config_path: str | None) -> RunConfig:
    """Load configuration from TOML file or use defaults.

    Args:
        config_path: Path to config file, or None to use default.

    Returns:
        RunConfig loaded from file or defaults.

    Raises:
        ConfigError: If config file is invalid.
    """
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH

    # If no config file exists, use defaults
    if not path.exists():
        return _get_default_config()

    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except Exception as e:
        raise ConfigError(f"Failed to load config from {path}: {e}") from e

    return _parse_config(data)


def _get_default_config() -> RunConfig:
    """Get default configuration when no config file exists."""
    default_models = (
        ModelConfig(
            name="gpt-4o",
            provider="openai",
            model_id="gpt-4o",
            temperature=0.2,
            max_tokens=2048,
            timeout_seconds=60,
            weight=1.0,
        ),
        ModelConfig(
            name="claude-3-5",
            provider="anthropic",
            model_id="claude-3-5-sonnet-20241022",
            temperature=0.2,
            max_tokens=2048,
            timeout_seconds=60,
            weight=1.0,
        ),
    )

    # Mediator must be separate from participants
    default_mediator = ModelConfig(
        name="gemini-1.5-pro",
        provider="gemini",
        model_id="gemini-1.5-pro",
        temperature=0.2,
        max_tokens=2048,
        timeout_seconds=60,
        weight=1.0,
    )

    return RunConfig(
        models=default_models,
        mediator=default_mediator,
        max_rounds=3,
        approval_ratio=0.67,
        change_threshold=0.10,
        max_context_tokens=None,
        strict_json=False,
        verbose=False,
        share_mode=ShareMode.DIGEST,
    )


def _parse_config(data: dict[str, Any]) -> RunConfig:
    """Parse TOML data into RunConfig.

    Args:
        data: Parsed TOML data.

    Returns:
        Validated RunConfig.

    Raises:
        ConfigError: If config is invalid.
    """
    # Parse model configurations
    model_list = data.get("model", [])
    if not model_list:
        raise ConfigError("Config must define at least one [[model]] entry")

    models = []
    model_names = set()
    for i, model_data in enumerate(model_list):
        try:
            model = _parse_model_config(model_data)
            if model.name in model_names:
                raise ConfigError(f"Duplicate model name: {model.name}")
            model_names.add(model.name)
            models.append(model)
        except (ValueError, TypeError) as e:
            raise ConfigError(f"Invalid model config at index {i}: {e}") from e

    # Parse mediator config
    mediator_data = data.get("mediator", {})
    if not mediator_data:
        raise ConfigError("Config must define [mediator] section")

    try:
        mediator = _parse_model_config(mediator_data)
    except (ValueError, TypeError) as e:
        raise ConfigError(f"Invalid mediator config: {e}") from e

    # Validate mediator is not in participant list
    if mediator.name in model_names:
        raise ConfigError(
            f"Mediator '{mediator.name}' must not appear in participant model list"
        )

    # Parse run configuration
    run_data = data.get("run", {})
    try:
        max_rounds = run_data.get("max_rounds", 3)
        approval_ratio = run_data.get("approval_ratio", 0.67)
        change_threshold = run_data.get("change_threshold", 0.10)
        max_context_tokens = run_data.get("max_context_tokens")
        strict_json = run_data.get("strict_json", False)
        verbose = run_data.get("verbose", False)
        share_mode_str = run_data.get("share_mode", "digest")

        # Validate share_mode
        try:
            share_mode = ShareMode(share_mode_str)
        except ValueError:
            raise ConfigError(
                f"Invalid share_mode '{share_mode_str}', must be 'digest' or 'raw'"
            )

        return RunConfig(
            models=tuple(models),
            mediator=mediator,
            max_rounds=max_rounds,
            approval_ratio=approval_ratio,
            change_threshold=change_threshold,
            max_context_tokens=max_context_tokens,
            strict_json=strict_json,
            verbose=verbose,
            share_mode=share_mode,
        )
    except (ValueError, TypeError) as e:
        raise ConfigError(f"Invalid run config: {e}") from e


def _parse_model_config(data: dict[str, Any]) -> ModelConfig:
    """Parse a model configuration from TOML data.

    Args:
        data: Model config dict from TOML.

    Returns:
        ModelConfig instance.

    Raises:
        ValueError: If required fields are missing or invalid.
    """
    required_fields = ["name", "provider", "model_id"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    return ModelConfig(
        name=str(data["name"]),
        provider=str(data["provider"]),
        model_id=str(data["model_id"]),
        temperature=float(data.get("temperature", 0.2)),
        max_tokens=int(data.get("max_tokens", 2048)),
        timeout_seconds=int(data.get("timeout_seconds", 60)),
        weight=float(data.get("weight", 1.0)),
    )


def _apply_overrides(
    config: RunConfig,
    overrides: ConfigOverrides,
    user_prefs: UserPreferences | None = None,
) -> RunConfig:
    """Apply user preferences and CLI overrides to config.

    Fallback chain: CLI flags -> user config -> project config

    Args:
        config: Base configuration.
        overrides: CLI flag overrides.
        user_prefs: User preferences from user config.

    Returns:
        Updated RunConfig.

    Raises:
        ConfigError: If override values are invalid.
    """
    if user_prefs is None:
        user_prefs = UserPreferences.empty()

    models = config.models
    mediator = config.mediator

    # Build model name map for lookup (includes all defined models)
    model_map = {model.name: model for model in config.models}
    model_map[config.mediator.name] = config.mediator

    # Determine which models to use (CLI -> user prefs -> config)
    model_names: list[str] | None = None
    if overrides.models is not None:
        model_names = [name.strip() for name in overrides.models.split(",") if name.strip()]
        if not model_names:
            raise ConfigError("--models flag cannot be empty")
    elif user_prefs.default_models:
        model_names = list(user_prefs.default_models)

    if model_names is not None:
        selected_models = []
        for name in model_names:
            model = _resolve_model(name, model_map, user_prefs)
            selected_models.append(model)
        models = tuple(selected_models)

    # Determine mediator (CLI -> user prefs -> config)
    mediator_name: str | None = None
    if overrides.mediator:
        mediator_name = overrides.mediator
    elif user_prefs.default_mediator:
        mediator_name = user_prefs.default_mediator

    if mediator_name is not None:
        mediator = _resolve_model(mediator_name, model_map, user_prefs)

    # Validate mediator is not in participant list
    if mediator in models:
        raise ConfigError(
            f"Mediator '{mediator.name}' cannot also be a participant model"
        )

    # Apply share_mode override
    share_mode = config.share_mode
    if overrides.share_mode:
        try:
            share_mode = ShareMode(overrides.share_mode)
        except ValueError:
            raise ConfigError(
                f"Invalid --share-mode '{overrides.share_mode}', must be 'digest' or 'raw'"
            )

    return RunConfig(
        models=models,
        mediator=mediator,
        max_rounds=overrides.rounds if overrides.rounds is not None else config.max_rounds,
        approval_ratio=(
            overrides.approval_ratio
            if overrides.approval_ratio is not None
            else config.approval_ratio
        ),
        change_threshold=(
            overrides.change_threshold
            if overrides.change_threshold is not None
            else config.change_threshold
        ),
        max_context_tokens=(
            overrides.max_context_tokens
            if overrides.max_context_tokens is not None
            else config.max_context_tokens
        ),
        strict_json=(
            overrides.strict_json if overrides.strict_json is not None else config.strict_json
        ),
        verbose=overrides.verbose if overrides.verbose is not None else config.verbose,
        share_mode=share_mode,
    )


def _resolve_model(
    name: str,
    model_map: dict[str, ModelConfig],
    user_prefs: UserPreferences,
) -> ModelConfig:
    """Resolve a model name or shorthand to a ModelConfig.

    Args:
        name: Model name, shorthand (gpt, claude, gemini), or model_id.
        model_map: Map of known model names to ModelConfig.
        user_prefs: User preferences with custom shorthand mappings.

    Returns:
        ModelConfig for the resolved model.

    Raises:
        ConfigError: If model cannot be resolved.
    """
    # First, check if it's a known model name from config
    if name in model_map:
        return model_map[name]

    # Check if it's a shorthand (gpt, claude, gemini)
    if is_shorthand(name, user_prefs):
        provider, model_id = expand_shorthand(name, user_prefs)
        # Create a new ModelConfig for this shorthand
        return ModelConfig(
            name=name,
            provider=provider,
            model_id=model_id,
            temperature=0.2,
            max_tokens=2048,
            timeout_seconds=60,
            weight=1.0,
        )

    # Check if it's a raw model_id that matches a known model
    for model in model_map.values():
        if model.model_id == name:
            return model

    # Try to infer provider from model_id prefix and create ad-hoc config
    provider = _infer_provider(name)
    if provider:
        return ModelConfig(
            name=name,
            provider=provider,
            model_id=name,
            temperature=0.2,
            max_tokens=2048,
            timeout_seconds=60,
            weight=1.0,
        )

    # Unknown model
    available = ", ".join(sorted(model_map.keys()))
    shorthands = ", ".join(sorted(PROVIDER_SHORTHANDS.keys()))
    raise ConfigError(
        f"Model '{name}' not found. Available: {available}. Shorthands: {shorthands}"
    )


def _infer_provider(model_id: str) -> str | None:
    """Infer provider from model ID prefix.

    Args:
        model_id: The model identifier.

    Returns:
        Provider name or None if cannot infer.
    """
    model_lower = model_id.lower()
    if model_lower.startswith("gpt") or model_lower.startswith("o1"):
        return "openai"
    if model_lower.startswith("claude"):
        return "anthropic"
    if model_lower.startswith("gemini"):
        return "gemini"
    return None
