"""Token estimation for context budget tracking."""

from __future__ import annotations

from aicx.types import Digest, PromptRequest, Response


def estimate_tokens(text: str) -> int:
    """
    Estimate token count using chars/4 ratio.

    This is a simple approximation that works reasonably well for English text.
    In v1, we avoid external tokenizer dependencies.

    Args:
        text: Text to estimate tokens for

    Returns:
        Estimated token count (rounded up)
    """
    if not text:
        return 0

    # chars/4 is a common approximation for English text
    # Round up to avoid underestimating
    return (len(text) + 3) // 4


def count_prompt_tokens(request: PromptRequest) -> int:
    """
    Count tokens in a prompt request.

    Includes:
    - System prompt
    - User prompt
    - Digest (if present)
    - Candidate answer (if present)

    Args:
        request: Prompt request to count tokens for

    Returns:
        Total estimated token count
    """
    total = 0

    # System and user prompts
    total += estimate_tokens(request.system_prompt)
    total += estimate_tokens(request.user_prompt)

    # Digest components
    if request.input_digest:
        total += _count_digest_tokens(request.input_digest)

    # Candidate answer
    if request.candidate_answer:
        total += estimate_tokens(request.candidate_answer)

    return total


def count_response_tokens(response: Response) -> int:
    """
    Count tokens in a response.

    Includes:
    - Answer text
    - Objections
    - Missing items
    - Edits

    Args:
        response: Response to count tokens for

    Returns:
        Total estimated token count
    """
    total = 0

    # Answer
    total += estimate_tokens(response.answer)

    # Objections
    for objection in response.objections:
        total += estimate_tokens(objection)

    # Missing items
    for missing in response.missing:
        total += estimate_tokens(missing)

    # Edits
    for edit in response.edits:
        total += estimate_tokens(edit)

    return total


def _count_digest_tokens(digest: Digest) -> int:
    """
    Count tokens in a digest.

    Args:
        digest: Digest to count tokens for

    Returns:
        Total estimated token count
    """
    total = 0

    for point in digest.common_points:
        total += estimate_tokens(point)

    for objection in digest.objections:
        total += estimate_tokens(objection)

    for missing in digest.missing:
        total += estimate_tokens(missing)

    for edit in digest.suggested_edits:
        total += estimate_tokens(edit)

    return total
