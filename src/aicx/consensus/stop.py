"""Stop conditions and change-threshold logic."""

from __future__ import annotations

import math
from typing import Sequence

from aicx.types import Response, RunConfig


def check_consensus_reached(
    approval_count: int,
    critical_objections: Sequence[str],
    config: RunConfig,
) -> bool:
    """
    Check if consensus criteria are met.

    Consensus is reached when:
    - approvals >= ceil(2/3 * participants)
    - critical_objections == 0

    Args:
        approval_count: Number of approvals received
        critical_objections: Sequence of critical objections
        config: Run configuration

    Returns:
        True if consensus is reached, False otherwise
    """
    quorum = config.quorum
    has_quorum = approval_count >= quorum
    no_critical = len(critical_objections) == 0

    return has_quorum and no_critical


def check_max_rounds_reached(current_round: int, config: RunConfig) -> bool:
    """
    Check if maximum rounds have been reached.

    Args:
        current_round: Current round number (1-indexed)
        config: Run configuration

    Returns:
        True if max rounds reached, False otherwise
    """
    return current_round >= config.max_rounds


def check_below_change_threshold(
    previous_candidate: str,
    new_candidate: str,
    config: RunConfig,
) -> bool:
    """
    Check if change between candidates is below threshold.

    Uses normalized Levenshtein distance on whitespace-tokenized text.
    Default threshold: < 10% change (0.10).

    Args:
        previous_candidate: Previous candidate answer
        new_candidate: New candidate answer
        config: Run configuration

    Returns:
        True if change is below threshold, False otherwise
    """
    change_ratio = compute_change_ratio(previous_candidate, new_candidate)
    return change_ratio < config.change_threshold


def check_no_changes_proposed(critiques: Sequence[Response]) -> bool:
    """
    Check if no participant proposed any changes.

    A change is proposed if the critique contains:
    - Any objections
    - Any missing items
    - Any suggested edits

    Args:
        critiques: Sequence of critique responses

    Returns:
        True if no changes proposed, False otherwise
    """
    for critique in critiques:
        has_objections = len(critique.objections) > 0
        has_missing = len(critique.missing) > 0
        has_edits = len(critique.edits) > 0

        if has_objections or has_missing or has_edits:
            return False

    return True


def compute_change_ratio(text1: str, text2: str) -> float:
    """
    Compute normalized change ratio between two texts.

    Uses Levenshtein distance on whitespace-tokenized text.
    Normalizes by the length of the longer text.

    Args:
        text1: First text
        text2: Second text

    Returns:
        Change ratio in [0, 1], where 0 = identical, 1 = completely different
    """
    # Tokenize on whitespace
    tokens1 = text1.split()
    tokens2 = text2.split()

    # Compute Levenshtein distance
    distance = _levenshtein_distance(tokens1, tokens2)

    # Normalize by length of longer sequence
    max_length = max(len(tokens1), len(tokens2))
    if max_length == 0:
        return 0.0

    return distance / max_length


def _levenshtein_distance(seq1: Sequence[str], seq2: Sequence[str]) -> int:
    """
    Compute Levenshtein distance between two sequences.

    Uses dynamic programming with O(min(m,n)) space optimization.

    Args:
        seq1: First sequence
        seq2: Second sequence

    Returns:
        Levenshtein distance (minimum edit operations)
    """
    if len(seq1) < len(seq2):
        seq1, seq2 = seq2, seq1

    if len(seq2) == 0:
        return len(seq1)

    # Use rolling arrays to save space
    previous_row = list(range(len(seq2) + 1))
    current_row = [0] * (len(seq2) + 1)

    for i, c1 in enumerate(seq1):
        current_row[0] = i + 1

        for j, c2 in enumerate(seq2):
            # Cost of insertion, deletion, substitution
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (0 if c1 == c2 else 1)

            current_row[j + 1] = min(insertions, deletions, substitutions)

        previous_row, current_row = current_row, previous_row

    return previous_row[len(seq2)]


def should_stop(
    current_round: int,
    approval_count: int,
    critical_objections: Sequence[str],
    previous_candidate: str | None,
    new_candidate: str,
    critiques: Sequence[Response],
    config: RunConfig,
) -> tuple[bool, str]:
    """
    Determine if consensus loop should stop.

    Checks all stop conditions in order:
    1. Consensus reached
    2. Max rounds reached
    3. Change below threshold
    4. No changes proposed

    Args:
        current_round: Current round number (1-indexed)
        approval_count: Number of approvals
        critical_objections: Sequence of critical objections
        previous_candidate: Previous candidate answer (None for round 1)
        new_candidate: New candidate answer
        critiques: Sequence of critique responses
        config: Run configuration

    Returns:
        Tuple of (should_stop, reason)
    """
    # Check consensus first
    if check_consensus_reached(approval_count, critical_objections, config):
        return (True, "consensus_reached")

    # Check max rounds
    if check_max_rounds_reached(current_round, config):
        return (True, "max_rounds_reached")

    # Check change threshold (only if we have a previous candidate)
    if previous_candidate is not None:
        if check_below_change_threshold(previous_candidate, new_candidate, config):
            return (True, "below_change_threshold")

    # Check no changes proposed
    if check_no_changes_proposed(critiques):
        return (True, "no_changes_proposed")

    return (False, "")
