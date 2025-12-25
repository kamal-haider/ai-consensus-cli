"""Interactive help assistant for CLI questions."""

from __future__ import annotations

import sys

from aicx.models.factory import create_provider
from aicx.types import ModelConfig, PromptRequest, Role
from aicx.user_config import (
    DEFAULT_PROVIDER_MODELS,
    check_api_key,
    load_user_preferences,
)


HELP_SYSTEM_PROMPT = """You are a helpful assistant for the AI Consensus CLI (aicx).

Your role is to answer questions about how to use the CLI tool. Be concise and actionable.

The CLI has these key features:
- Sends prompts to multiple AI models and synthesizes consensus answers
- Models are participants that answer; a mediator synthesizes responses
- Supports OpenAI (gpt-*), Anthropic (claude-*), and Google (gemini-*) models

Key commands and flags:
- `aicx "prompt"` - Send a prompt to default models
- `--models gpt,claude,gemini` - Use specific models (shorthands or full IDs)
- `--mediator NAME` - Set the mediator model
- `--rounds N` - Set max consensus rounds (default: 3)
- `--setup` - Interactive wizard to configure defaults
- `--status` - Show current configuration and API key status
- `--verbose` - Enable detailed logging
- `--config PATH` - Use custom config file

Configuration:
- User config: ~/.config/aicx/config.toml
- Project config: config/config.toml
- Fallback chain: CLI flags -> user config -> project config -> defaults

Shorthands:
- `gpt` -> OpenAI's default model
- `claude` -> Anthropic's default model
- `gemini` -> Google's default model

API Keys (environment variables):
- OPENAI_API_KEY
- ANTHROPIC_API_KEY
- GEMINI_API_KEY

Keep answers brief (1-3 sentences when possible). If the user asks about something unrelated to the CLI, politely redirect them to use aicx for general questions.

If the user asks how to configure something, suggest using --setup.
If they ask about current settings, suggest using --status."""


def run_help_assistant(question: str) -> int:
    """Run the help assistant to answer a CLI question.

    Args:
        question: The user's question about the CLI.

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    # Find an available provider for the assistant
    provider_config = _get_assistant_provider()
    if provider_config is None:
        print("No API keys configured. Please set one of:")
        print("  - OPENAI_API_KEY")
        print("  - ANTHROPIC_API_KEY")
        print("  - GEMINI_API_KEY")
        print()
        print("Or run: aicx --setup")
        return 1

    try:
        provider = create_provider(provider_config)
    except Exception as e:
        sys.stderr.write(f"Failed to create provider: {e}\n")
        return 2

    # Create the request
    request = PromptRequest(
        system_prompt=HELP_SYSTEM_PROMPT,
        user_prompt=question,
        round_index=1,
        role=Role.PARTICIPANT,
    )

    try:
        response = provider.create_chat_completion(request)
        print(response.answer)
        return 0
    except Exception as e:
        sys.stderr.write(f"Error getting help: {e}\n")
        return 2


def _get_assistant_provider() -> ModelConfig | None:
    """Get a model config for the assistant.

    Prefers user's configured mediator, falls back to any available provider.

    Returns:
        ModelConfig or None if no providers available.
    """
    prefs = load_user_preferences()

    # Try user's configured mediator first
    if prefs.default_mediator:
        provider = _infer_provider(prefs.default_mediator)
        if provider and check_api_key(provider):
            return ModelConfig(
                name="assistant",
                provider=provider,
                model_id=prefs.default_mediator,
                temperature=0.3,
                max_tokens=500,
                timeout_seconds=30,
                weight=1.0,
            )

    # Try providers in order of preference
    for provider_name in ["anthropic", "openai", "gemini"]:
        if check_api_key(provider_name):
            model_id = DEFAULT_PROVIDER_MODELS[provider_name]
            return ModelConfig(
                name="assistant",
                provider=provider_name,
                model_id=model_id,
                temperature=0.3,
                max_tokens=500,
                timeout_seconds=30,
                weight=1.0,
            )

    return None


def _infer_provider(model_id: str) -> str | None:
    """Infer provider from model ID."""
    model_lower = model_id.lower()
    if model_lower.startswith("gpt") or model_lower.startswith("o1"):
        return "openai"
    if model_lower.startswith("claude"):
        return "anthropic"
    if model_lower.startswith("gemini"):
        return "gemini"
    return None
