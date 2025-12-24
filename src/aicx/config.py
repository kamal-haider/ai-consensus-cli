"""Configuration loading and validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from aicx.types import ModelConfig, RunConfig


DEFAULT_CONFIG_PATH = Path("config/config.toml")


@dataclass(frozen=True)
class ConfigOverrides:
    models: str | None
    mediator: str | None
    rounds: int | None
    approval_ratio: float | None
    change_threshold: float | None
    share_mode: str | None
    verbose: bool | None


def load_config(
    config_path: str | None,
    *,
    models: str | None,
    mediator: str | None,
    rounds: int | None,
    approval_ratio: float | None,
    change_threshold: float | None,
    share_mode: str | None,
    verbose: bool | None,
) -> RunConfig:
    overrides = ConfigOverrides(
        models=models,
        mediator=mediator,
        rounds=rounds,
        approval_ratio=approval_ratio,
        change_threshold=change_threshold,
        share_mode=share_mode,
        verbose=verbose,
    )

    # Placeholder: load defaults and config file; merge overrides.
    # TODO: parse TOML from config_path or DEFAULT_CONFIG_PATH.
    # TODO: validate config values and uniqueness.
    _ = config_path

    default_models = [
        ModelConfig(
            name="gpt-4o",
            provider="openai",
            model_id="gpt-4o",
            temperature=0.2,
            max_tokens=2048,
            timeout_seconds=60,
            weight=1.0,
        )
    ]

    run_config = RunConfig(
        models=default_models,
        mediator=default_models[0],
        max_rounds=3,
        quorum=1,
        approval_ratio=0.67,
        change_threshold=0.10,
        verbose=bool(overrides.verbose),
        share_mode="digest",
    )

    return apply_overrides(run_config, overrides)


def apply_overrides(config: RunConfig, overrides: ConfigOverrides) -> RunConfig:
    models = config.models
    mediator = config.mediator

    if overrides.models:
        names = [name.strip() for name in overrides.models.split(",") if name.strip()]
        models = [model for model in config.models if model.name in names]

    if overrides.mediator:
        for model in config.models:
            if model.name == overrides.mediator:
                mediator = model
                break

    return RunConfig(
        models=models,
        mediator=mediator,
        max_rounds=overrides.rounds or config.max_rounds,
        quorum=config.quorum,
        approval_ratio=overrides.approval_ratio or config.approval_ratio,
        change_threshold=overrides.change_threshold or config.change_threshold,
        verbose=bool(overrides.verbose) if overrides.verbose is not None else config.verbose,
        share_mode=overrides.share_mode or config.share_mode,
    )


def resolve_model_names(names: Iterable[str], config: RunConfig) -> list[ModelConfig]:
    name_set = set(names)
    return [model for model in config.models if model.name in name_set]
