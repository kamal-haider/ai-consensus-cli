"""Interactive setup wizard for AI Consensus CLI."""

from __future__ import annotations

import sys

from aicx.user_config import (
    DEFAULT_PROVIDER_MODELS,
    UserPreferences,
    check_api_key,
    get_api_key_status,
    get_user_config_path,
    load_user_preferences,
    save_user_preferences,
)


# Available models for each provider
AVAILABLE_MODELS: dict[str, list[str]] = {
    "openai": ["gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
    "anthropic": [
        "claude-sonnet-4-20250514",
        "claude-opus-4-20250514",
        "claude-3-5-sonnet-20241022",
        "claude-3-opus-20240229",
    ],
    "gemini": ["gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"],
}


def run_setup() -> int:
    """Run the interactive setup wizard.

    Returns:
        Exit code (0 for success).
    """
    print("AI Consensus CLI - Setup Wizard")
    print("=" * 40)
    print()

    # Check API keys
    api_status = get_api_key_status()
    available_providers = [p for p, has_key in api_status.items() if has_key]

    print("API Key Status:")
    for provider, has_key in api_status.items():
        status = "OK" if has_key else "NOT SET"
        print(f"  {provider.upper()}: {status}")
    print()

    if not available_providers:
        print("No API keys found. Please set at least one of:")
        print("  - OPENAI_API_KEY")
        print("  - ANTHROPIC_API_KEY")
        print("  - GEMINI_API_KEY")
        print()
        print("Then run --setup again.")
        return 1

    # Load existing preferences
    existing = load_user_preferences()

    # Select default models
    print("Select default participant models:")
    print("(These will be used when you run 'aicx \"prompt\"' without --models)")
    print()

    selected_models: list[str] = []
    for provider in available_providers:
        models = AVAILABLE_MODELS.get(provider, [])
        if not models:
            continue

        print(f"{provider.upper()} models:")
        for i, model in enumerate(models, 1):
            default_marker = " (current default)" if model == DEFAULT_PROVIDER_MODELS.get(provider) else ""
            print(f"  {i}. {model}{default_marker}")
        print(f"  0. Skip {provider}")
        print()

        while True:
            choice = _prompt(f"Select {provider} model [1]: ", "1")
            try:
                idx = int(choice)
                if idx == 0:
                    break
                if 1 <= idx <= len(models):
                    selected_models.append(models[idx - 1])
                    break
                print(f"Please enter 0-{len(models)}")
            except ValueError:
                print("Please enter a number")

    if not selected_models:
        print()
        print("No models selected. Using built-in defaults.")
        selected_models = []

    print()
    print("-" * 40)
    print()

    # Select mediator
    print("Select default mediator:")
    print("(The mediator synthesizes answers and guides consensus)")
    print()

    all_models: list[tuple[str, str]] = []  # (provider, model_id)
    for provider in available_providers:
        models = AVAILABLE_MODELS.get(provider, [])
        for model in models:
            if model not in selected_models:  # Mediator should differ from participants
                all_models.append((provider, model))

    if not all_models:
        # If all models are selected as participants, show all anyway
        for provider in available_providers:
            models = AVAILABLE_MODELS.get(provider, [])
            for model in models:
                all_models.append((provider, model))

    for i, (provider, model) in enumerate(all_models, 1):
        print(f"  {i}. {model} ({provider})")
    print()

    selected_mediator: str | None = None
    while True:
        choice = _prompt("Select mediator [1]: ", "1")
        try:
            idx = int(choice)
            if 1 <= idx <= len(all_models):
                selected_mediator = all_models[idx - 1][1]
                break
            print(f"Please enter 1-{len(all_models)}")
        except ValueError:
            print("Please enter a number")

    print()
    print("-" * 40)
    print()

    # Configure shorthands
    print("Shorthand Configuration:")
    print("(Allows you to use 'gpt', 'claude', 'gemini' as shortcuts)")
    print()

    shorthand_models: dict[str, str] = {}
    for shorthand, provider in [("gpt", "openai"), ("claude", "anthropic"), ("gemini", "gemini")]:
        if provider not in available_providers:
            continue

        models = AVAILABLE_MODELS.get(provider, [])
        if not models:
            continue

        current = existing.shorthand_models.get(shorthand, DEFAULT_PROVIDER_MODELS.get(provider, ""))
        print(f"'{shorthand}' shorthand maps to:")
        for i, model in enumerate(models, 1):
            current_marker = " (current)" if model == current else ""
            print(f"  {i}. {model}{current_marker}")
        print()

        while True:
            choice = _prompt(f"Select model for '{shorthand}' [1]: ", "1")
            try:
                idx = int(choice)
                if 1 <= idx <= len(models):
                    shorthand_models[shorthand] = models[idx - 1]
                    break
                print(f"Please enter 1-{len(models)}")
            except ValueError:
                print("Please enter a number")

    print()
    print("=" * 40)
    print()

    # Summary
    print("Configuration Summary:")
    print()
    if selected_models:
        print(f"  Default models: {', '.join(selected_models)}")
    else:
        print("  Default models: (using built-in defaults)")
    print(f"  Default mediator: {selected_mediator}")
    print()
    print("  Shorthands:")
    for shorthand, model_id in sorted(shorthand_models.items()):
        print(f"    {shorthand} -> {model_id}")
    print()

    # Confirm and save
    confirm = _prompt("Save this configuration? [Y/n]: ", "y")
    if confirm.lower() not in ("y", "yes", ""):
        print("Configuration not saved.")
        return 0

    # Save preferences
    prefs = UserPreferences(
        default_models=tuple(selected_models),
        default_mediator=selected_mediator,
        shorthand_models=shorthand_models,
    )
    save_user_preferences(prefs)

    config_path = get_user_config_path()
    print()
    print(f"Configuration saved to: {config_path}")
    print()
    print("You can now run:")
    print('  aicx "Your prompt here"')
    print()

    return 0


def run_status() -> int:
    """Show current configuration status.

    Returns:
        Exit code (0 for success).
    """
    print("AI Consensus CLI - Status")
    print("=" * 40)
    print()

    # API key status
    api_status = get_api_key_status()
    print("API Keys:")
    for provider, has_key in api_status.items():
        status = "OK" if has_key else "NOT SET"
        print(f"  {provider.upper()}: {status}")
    print()

    # User config
    config_path = get_user_config_path()
    prefs = load_user_preferences()

    print("Configuration:")
    print(f"  User config: {config_path}")
    if config_path.exists():
        print("  Status: Found")
    else:
        print("  Status: Not configured (run --setup)")
    print()

    # Defaults
    print("Defaults:")
    if prefs.default_models:
        print(f"  Models: {', '.join(prefs.default_models)}")
    else:
        print("  Models: (built-in defaults)")

    if prefs.default_mediator:
        print(f"  Mediator: {prefs.default_mediator}")
    else:
        print("  Mediator: (built-in default)")
    print()

    # Shorthands
    print("Shorthand Aliases:")
    if prefs.shorthand_models:
        for shorthand, model_id in sorted(prefs.shorthand_models.items()):
            print(f"  {shorthand} -> {model_id}")
    else:
        print("  (using built-in defaults)")
        for shorthand, provider in [("gpt", "openai"), ("claude", "anthropic"), ("gemini", "gemini")]:
            model_id = DEFAULT_PROVIDER_MODELS.get(provider, "")
            if model_id:
                print(f"  {shorthand} -> {model_id}")
    print()

    return 0


def _prompt(message: str, default: str = "") -> str:
    """Prompt user for input.

    Args:
        message: Prompt message.
        default: Default value if user presses Enter.

    Returns:
        User input or default.
    """
    try:
        response = input(message)
        return response.strip() if response.strip() else default
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)
