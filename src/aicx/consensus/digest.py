"""Digest construction and ordering logic."""

from __future__ import annotations

from collections import Counter
from typing import Sequence

from aicx.types import Digest, Response


def build_digest(responses: Sequence[Response]) -> Digest:
    """
    Construct a digest from participant responses.

    Digest contains:
    - common_points: shared claims across answers
    - objections: notable conflicts or contradictions
    - missing: key points absent in most answers
    - suggested_edits: concise fix labels

    All items are deterministically ordered by:
    1. Frequency (descending)
    2. Alphabetical order (for ties)

    Args:
        responses: Sequence of Response objects from participants

    Returns:
        Digest object with sorted items
    """
    if not responses:
        return Digest(
            common_points=(),
            objections=(),
            missing=(),
            suggested_edits=(),
        )

    # Extract all objections, missing items, and edits from responses
    all_objections: list[str] = []
    all_missing: list[str] = []
    all_edits: list[str] = []

    for response in responses:
        all_objections.extend(response.objections)
        all_missing.extend(response.missing)
        all_edits.extend(response.edits)

    # For common points, we need to extract shared claims from answers
    # In this phase, we'll use a simple heuristic: extract sentences
    # and find those that appear in multiple answers
    common_points = _extract_common_points(responses)

    # Sort items deterministically: by frequency (desc), then alphabetically
    sorted_objections = _sort_by_frequency_and_alpha(all_objections)
    sorted_missing = _sort_by_frequency_and_alpha(all_missing)
    sorted_edits = _sort_by_frequency_and_alpha(all_edits)

    return Digest(
        common_points=tuple(common_points),
        objections=tuple(sorted_objections),
        missing=tuple(sorted_missing),
        suggested_edits=tuple(sorted_edits),
    )


def _extract_common_points(responses: Sequence[Response]) -> list[str]:
    """
    Extract common points from participant answers.

    Uses simple sentence splitting and finds sentences that appear
    in multiple answers (at least 50% of responses).

    Args:
        responses: Sequence of Response objects

    Returns:
        List of common points, sorted by frequency then alphabetically
    """
    if not responses:
        return []

    # Extract sentences from all answers
    all_sentences: list[str] = []
    for response in responses:
        sentences = _split_into_sentences(response.answer)
        all_sentences.extend(sentences)

    # Count sentence occurrences
    sentence_counts = Counter(all_sentences)

    # Keep sentences that appear in at least 50% of responses
    threshold = len(responses) * 0.5
    common = [sent for sent, count in sentence_counts.items() if count >= threshold]

    # Sort by frequency (desc) then alphabetically
    common_with_counts = [(sent, sentence_counts[sent]) for sent in common]
    common_with_counts.sort(key=lambda x: (-x[1], x[0]))

    return [sent for sent, _ in common_with_counts]


def _split_into_sentences(text: str) -> list[str]:
    """
    Split text into sentences using simple heuristics.

    Args:
        text: Input text

    Returns:
        List of sentences, normalized (stripped and lowercased)
    """
    # Simple sentence splitting on common terminators
    # Normalize by stripping whitespace and converting to lowercase
    sentences = []
    for delimiter in ['. ', '! ', '? ', '\n']:
        text = text.replace(delimiter, '|SENT|')

    raw_sentences = text.split('|SENT|')
    for sent in raw_sentences:
        sent = sent.strip()
        if sent:
            sentences.append(sent)

    return sentences


def _sort_by_frequency_and_alpha(items: Sequence[str]) -> list[str]:
    """
    Sort items by frequency (descending) then alphabetically.

    Args:
        items: Sequence of strings

    Returns:
        Sorted list with duplicates removed
    """
    if not items:
        return []

    # Count occurrences
    counts = Counter(items)

    # Sort by frequency (desc) then alphabetically
    sorted_items = sorted(counts.items(), key=lambda x: (-x[1], x[0]))

    # Return just the items (not counts)
    return [item for item, _ in sorted_items]


def update_digest_from_critiques(
    previous_digest: Digest,
    critiques: Sequence[Response],
) -> Digest:
    """
    Update digest based on new critique responses.

    This combines the previous digest with new objections, missing items,
    and suggested edits from critique responses.

    Args:
        previous_digest: Previous digest from earlier round
        critiques: Sequence of critique responses

    Returns:
        Updated Digest with merged and sorted items
    """
    # Collect all items from previous digest and new critiques
    all_objections = list(previous_digest.objections)
    all_missing = list(previous_digest.missing)
    all_edits = list(previous_digest.suggested_edits)

    for critique in critiques:
        all_objections.extend(critique.objections)
        all_missing.extend(critique.missing)
        all_edits.extend(critique.edits)

    # Sort deterministically
    sorted_objections = _sort_by_frequency_and_alpha(all_objections)
    sorted_missing = _sort_by_frequency_and_alpha(all_missing)
    sorted_edits = _sort_by_frequency_and_alpha(all_edits)

    # Keep common_points from previous digest (not updated in critiques)
    return Digest(
        common_points=previous_digest.common_points,
        objections=tuple(sorted_objections),
        missing=tuple(sorted_missing),
        suggested_edits=tuple(sorted_edits),
    )
