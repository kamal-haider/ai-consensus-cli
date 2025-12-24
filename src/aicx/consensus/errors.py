"""Consensus-specific error types and validation helpers."""

from __future__ import annotations

from aicx.logging import log_error
from aicx.types import AicxError, QuorumError, Response, RunConfig


class ZeroResponseError(AicxError):
    """All models failed to respond in a round (exit code 2)."""

    def __init__(self, message: str, round_index: int):
        super().__init__(message)
        self.round_index = round_index


def check_round_responses(
    responses: list[Response],
    config: RunConfig,
    round_index: int = 1,
) -> None:
    """
    Validate that sufficient models responded in a round.

    Raises:
        ZeroResponseError: If no models responded (all failed).
        QuorumError: If some models responded but below quorum threshold.

    Args:
        responses: List of successful responses from the round.
        config: Run configuration with quorum settings.
        round_index: Round number for error reporting.
    """
    num_responses = len(responses)
    required = config.quorum

    if num_responses == 0:
        msg = f"All models failed in round {round_index} (0 of {len(config.models)} responded)"
        log_error("ZeroResponseError", msg, round_index=round_index)
        raise ZeroResponseError(msg, round_index=round_index)

    if num_responses < required:
        msg = f"Insufficient responses in round {round_index}: got {num_responses}, need {required}"
        log_error("QuorumError", msg, round_index=round_index)
        raise QuorumError(
            msg,
            received=num_responses,
            required=required,
        )
