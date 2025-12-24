"""Response collection with failure tracking."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from aicx.logging import log_error
from aicx.types import ModelConfig, ProviderError, Response, RunConfig


@dataclass(frozen=True)
class FailedModel:
    """Record of a model that failed to respond."""

    name: str
    error: str
    code: str | None = None


def collect_responses_with_failures(
    models: tuple[ModelConfig, ...],
    prompt_fn: Callable[[ModelConfig], Response],
    config: RunConfig,
    round_index: int = 1,
) -> tuple[list[Response], tuple[str, ...]]:
    """
    Collect responses from models, tracking failures separately.

    Calls each model and catches ProviderError exceptions.
    Failed models are logged but don't abort the collection.

    Args:
        models: Models to query.
        prompt_fn: Function to call each model (takes ModelConfig, returns Response).
        config: Run configuration (for logging).
        round_index: Round number for logging.

    Returns:
        Tuple of (successful_responses, failed_model_names).
    """
    successful_responses: list[Response] = []
    failed_models: list[str] = []

    # Sort by name for deterministic ordering
    sorted_models = sorted(models, key=lambda m: m.name)

    for model in sorted_models:
        try:
            response = prompt_fn(model)
            successful_responses.append(response)
        except ProviderError as e:
            failed_models.append(model.name)
            log_error(
                error_type="ProviderError",
                message=str(e),
                round_index=round_index,
                model=model.name,
            )

    return successful_responses, tuple(failed_models)
