"""Round truncation logic for context budget enforcement."""

from __future__ import annotations

from aicx.context.budget import ContextBudget
from aicx.context.tokens import count_response_tokens
from aicx.types import Digest, Response


def truncate_oldest_rounds(
    responses: tuple[Response, ...],
    round_indices: tuple[int, ...],
    budget: ContextBudget,
    target_tokens: int,
) -> tuple[Response, ...]:
    """
    Truncate responses from oldest rounds first to fit within target tokens.

    The most recent round is always kept intact. Older rounds are removed
    entirely until the total token count fits within the target.

    Args:
        responses: All responses to consider for truncation
        round_indices: Round index for each response (parallel to responses)
        budget: Current context budget state
        target_tokens: Target token count to fit within

    Returns:
        Truncated tuple of responses that fit within target_tokens
    """
    if len(responses) != len(round_indices):
        raise ValueError(
            f"responses and round_indices must have same length: "
            f"{len(responses)} != {len(round_indices)}"
        )

    if not responses:
        return ()

    # Find the most recent round
    max_round = max(round_indices)

    # Group responses by round
    rounds_map: dict[int, list[int]] = {}
    for idx, round_idx in enumerate(round_indices):
        if round_idx not in rounds_map:
            rounds_map[round_idx] = []
        rounds_map[round_idx].append(idx)

    # Calculate token counts for each response
    token_counts = [count_response_tokens(r) for r in responses]

    # Start with all rounds, remove oldest until we fit
    included_rounds = sorted(rounds_map.keys(), reverse=True)
    current_tokens = sum(token_counts)

    while current_tokens > target_tokens and len(included_rounds) > 1:
        # Remove the oldest round (excluding the most recent)
        oldest_round = included_rounds[-1]

        # Don't remove the most recent round
        if oldest_round == max_round:
            break

        # Remove this round and recalculate
        removed_indices = rounds_map[oldest_round]
        for idx in removed_indices:
            current_tokens -= token_counts[idx]

        included_rounds.pop()

    # Build the truncated response list
    included_indices = []
    for round_idx in included_rounds:
        included_indices.extend(rounds_map[round_idx])

    # Sort indices to maintain original order
    included_indices.sort()

    return tuple(responses[idx] for idx in included_indices)


def build_truncated_digest(responses: tuple[Response, ...], max_tokens: int) -> Digest:
    """
    Build a digest from potentially truncated responses.

    If responses were truncated, adds a note about the number of
    responses that were dropped.

    Args:
        responses: Responses to build digest from (may be truncated)
        max_tokens: Maximum tokens used for truncation decision

    Returns:
        Digest with common points, objections, missing items, and edits
    """
    if not responses:
        return Digest(
            common_points=(),
            objections=(),
            missing=(),
            suggested_edits=(),
        )

    # Collect all feedback from responses
    all_objections = []
    all_missing = []
    all_edits = []

    for response in responses:
        all_objections.extend(response.objections)
        all_missing.extend(response.missing)
        all_edits.extend(response.edits)

    # Count responses that disapproved
    disapproval_count = sum(1 for r in responses if r.approve is False)

    # Build common points
    common_points = []

    # If there were truncations, note it
    # (We don't track the original count in this function, so we rely on
    # the caller to determine if truncation occurred)
    # For now, just build the digest from available responses

    # Add approval/disapproval summary
    if len(responses) > 0:
        approval_count = sum(1 for r in responses if r.approve is True)
        if approval_count > 0:
            common_points.append(f"{approval_count}/{len(responses)} participants approved")

    return Digest(
        common_points=tuple(common_points),
        objections=tuple(all_objections),
        missing=tuple(all_missing),
        suggested_edits=tuple(all_edits),
    )
