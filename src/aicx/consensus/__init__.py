"""Consensus engine package."""

from aicx.consensus.digest import build_digest, update_digest_from_critiques
from aicx.consensus.runner import ConsensusContext, run_consensus
from aicx.consensus.stop import (
    check_consensus_reached,
    check_max_rounds_reached,
    check_below_change_threshold,
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
]
