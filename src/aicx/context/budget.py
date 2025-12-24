"""Context budget tracking for consensus rounds."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ContextBudget:
    """
    Track token usage across consensus rounds.

    Attributes:
        max_tokens: Maximum allowed tokens across all rounds
        used_tokens: Total tokens used so far
        round_usage: Token count for each round (indexed by round)
    """

    max_tokens: int
    used_tokens: int = 0
    round_usage: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        if self.max_tokens < 1:
            raise ValueError(f"max_tokens must be >= 1, got {self.max_tokens}")
        if self.used_tokens < 0:
            raise ValueError(f"used_tokens must be >= 0, got {self.used_tokens}")
        if self.used_tokens > self.max_tokens:
            raise ValueError(
                f"used_tokens ({self.used_tokens}) exceeds max_tokens ({self.max_tokens})"
            )


def track_usage(budget: ContextBudget, tokens: int, round_idx: int) -> ContextBudget:
    """
    Track token usage for a specific round.

    Returns a new ContextBudget with updated usage.

    Args:
        budget: Current budget state
        tokens: Number of tokens used in this round
        round_idx: Zero-based round index

    Returns:
        New ContextBudget with updated usage
    """
    if tokens < 0:
        raise ValueError(f"tokens must be >= 0, got {tokens}")

    # Extend round_usage to include this round if necessary
    new_round_usage = list(budget.round_usage)
    while len(new_round_usage) <= round_idx:
        new_round_usage.append(0)

    # Add tokens to the specific round
    new_round_usage[round_idx] += tokens

    # Calculate total used tokens
    new_used_tokens = sum(new_round_usage)

    return ContextBudget(
        max_tokens=budget.max_tokens,
        used_tokens=new_used_tokens,
        round_usage=tuple(new_round_usage),
    )


def would_exceed_budget(budget: ContextBudget, additional_tokens: int) -> bool:
    """
    Check if adding tokens would exceed the budget.

    Args:
        budget: Current budget state
        additional_tokens: Number of tokens to potentially add

    Returns:
        True if adding tokens would exceed max_tokens, False otherwise
    """
    if additional_tokens < 0:
        raise ValueError(f"additional_tokens must be >= 0, got {additional_tokens}")

    return budget.used_tokens + additional_tokens > budget.max_tokens
