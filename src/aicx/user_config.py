"""User configuration management for ~/.config/aicx/."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


# Default user config location
def get_user_config_dir() -> Path:
    """Get the user config directory path.

    Uses XDG_CONFIG_HOME if set, otherwise ~/.config/aicx/
    """
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config) / "aicx"
    return Path.home() / ".config" / "aicx"


def get_user_config_path() -> Path:
    """Get the user config file path."""
    return get_user_config_dir() / "config.toml"


# Provider shorthand mappings
PROVIDER_SHORTHANDS: dict[str, str] = {
    "gpt": "openai",
    "claude": "anthropic",
    "gemini": "gemini",
}

# Default model IDs for each provider (used when shorthand specified)
DEFAULT_PROVIDER_MODELS: dict[str, str] = {
    "openai": "gpt-4o",
    "anthropic": "claude-sonnet-4-20250514",
    "gemini": "gemini-2.0-flash-exp",
}


@dataclass(frozen=True)
class UserPreferences:
    """User preferences loaded from user config."""

    default_models: tuple[str, ...]  # Model names or shorthands
    default_mediator: str | None
    shorthand_models: dict[str, str]  # shorthand -> model_id mapping

    @classmethod
    def empty(cls) -> UserPreferences:
        """Create empty preferences (no user config)."""
        return cls(
            default_models=(),
            default_mediator=None,
            shorthand_models={},
        )


def load_user_preferences() -> UserPreferences:
    """Load user preferences from user config file.

    Returns:
        UserPreferences with user settings, or empty if no config exists.
    """
    config_path = get_user_config_path()
    if not config_path.exists():
        return UserPreferences.empty()

    try:
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
        return _parse_user_config(data)
    except Exception:
        # If user config is invalid, return empty preferences
        return UserPreferences.empty()


def _parse_user_config(data: dict[str, Any]) -> UserPreferences:
    """Parse user config TOML data."""
    defaults = data.get("defaults", {})
    shorthand = data.get("shorthand", {})

    default_models = defaults.get("models", [])
    if isinstance(default_models, str):
        default_models = [m.strip() for m in default_models.split(",") if m.strip()]

    return UserPreferences(
        default_models=tuple(default_models),
        default_mediator=defaults.get("mediator"),
        shorthand_models=dict(shorthand),
    )


def save_user_preferences(prefs: UserPreferences) -> None:
    """Save user preferences to user config file.

    Creates the config directory if it doesn't exist.
    """
    config_path = get_user_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    lines = ["# AI Consensus CLI User Configuration", ""]

    # Defaults section
    lines.append("[defaults]")
    if prefs.default_models:
        models_str = ", ".join(f'"{m}"' for m in prefs.default_models)
        lines.append(f"models = [{models_str}]")
    if prefs.default_mediator:
        lines.append(f'mediator = "{prefs.default_mediator}"')
    lines.append("")

    # Shorthand section
    if prefs.shorthand_models:
        lines.append("[shorthand]")
        for shorthand, model_id in sorted(prefs.shorthand_models.items()):
            lines.append(f'{shorthand} = "{model_id}"')
        lines.append("")

    config_path.write_text("\n".join(lines))


def check_api_key(provider: str) -> bool:
    """Check if API key is set for a provider.

    Args:
        provider: Provider name (openai, anthropic, gemini).

    Returns:
        True if the API key environment variable is set.
    """
    key_vars = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "gemini": "GEMINI_API_KEY",
    }
    var_name = key_vars.get(provider.lower())
    if not var_name:
        return False
    return bool(os.environ.get(var_name))


def get_api_key_status() -> dict[str, bool]:
    """Get API key status for all providers.

    Returns:
        Dict mapping provider name to whether API key is set.
    """
    return {
        "openai": check_api_key("openai"),
        "anthropic": check_api_key("anthropic"),
        "gemini": check_api_key("gemini"),
    }


def expand_shorthand(name: str, user_prefs: UserPreferences) -> tuple[str, str]:
    """Expand a model shorthand to provider and model_id.

    Args:
        name: Model name or shorthand (e.g., "gpt", "claude", "gpt-4o").
        user_prefs: User preferences with custom shorthand mappings.

    Returns:
        Tuple of (provider, model_id).
        Returns (name, name) if not a recognized shorthand.
    """
    # Check user-defined shorthands first
    if name in user_prefs.shorthand_models:
        model_id = user_prefs.shorthand_models[name]
        # Infer provider from shorthand name
        provider = PROVIDER_SHORTHANDS.get(name, "")
        if not provider:
            # Try to infer from model_id prefix
            if model_id.startswith("gpt"):
                provider = "openai"
            elif model_id.startswith("claude"):
                provider = "anthropic"
            elif model_id.startswith("gemini"):
                provider = "gemini"
        return (provider, model_id) if provider else (name, model_id)

    # Check built-in shorthands
    if name in PROVIDER_SHORTHANDS:
        provider = PROVIDER_SHORTHANDS[name]
        model_id = DEFAULT_PROVIDER_MODELS[provider]
        return (provider, model_id)

    # Not a shorthand - return as-is
    return ("", name)


def is_shorthand(name: str, user_prefs: UserPreferences | None = None) -> bool:
    """Check if a name is a recognized shorthand.

    Args:
        name: Model name to check.
        user_prefs: Optional user preferences.

    Returns:
        True if name is a shorthand (built-in or user-defined).
    """
    if name in PROVIDER_SHORTHANDS:
        return True
    if user_prefs and name in user_prefs.shorthand_models:
        return True
    return False
