"""Consensus engine package."""

from aicx.consensus.collection import FailedModel, collect_responses_with_failures
from aicx.consensus.digest import build_digest, update_digest_from_critiques
from aicx.consensus.errors import ZeroResponseError, check_round_responses
from aicx.consensus.runner import ConsensusContext, run_consensus
from aicx.consensus.stop import (
    check_below_change_threshold,
    check_consensus_reached,
    check_max_rounds_reached,
    check_no_changes_proposed,
    compute_change_ratio,
    should_stop,
)

__all__ = [
    "build_digest",
    "update_digest_from_critiques",
    "ConsensusContext",
    "run_consensus",
    "check_consensus_reached",
    "check_max_rounds_reached",
    "check_below_change_threshold",
    "check_no_changes_proposed",
    "compute_change_ratio",
    "should_stop",
    "ZeroResponseError",
    "check_round_responses",
    "FailedModel",
    "collect_responses_with_failures",
]
