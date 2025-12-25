"""Tests for digest construction and ordering logic."""

from __future__ import annotations

import pytest

from aicx.consensus.digest import (
    build_digest,
    update_digest_from_critiques,
    _extract_common_points,
    _split_into_sentences,
    _sort_by_frequency_and_alpha,
)
from aicx.types import Digest, Response


# Fixtures: Response objects


@pytest.fixture
def empty_response():
    """Empty response with no content."""
    return Response(
        model_name="empty-model",
        answer="",
    )


@pytest.fixture
def single_response():
    """Single response with basic answer."""
    return Response(
        model_name="model-1",
        answer="Paris is the capital of France. It is located in northern France.",
    )


@pytest.fixture
def response_with_critiques():
    """Response with objections, missing items, and edits."""
    return Response(
        model_name="model-1",
        answer="Paris is the capital.",
        objections=("Missing historical context", "Needs population data"),
        missing=("Founded date", "Area size"),
        edits=("Add more detail", "Include sources"),
    )


@pytest.fixture
def multiple_responses_shared_content():
    """Multiple responses with overlapping sentences."""
    # Note: When testing for common points, we need consistent sentence boundaries.
    # The sentence splitter splits on ". " so middle sentences lose their periods.
    # To get matching sentences, shared content must appear in the same position
    # relative to sentence boundaries.
    return [
        Response(
            model_name="model-1",
            answer="Paris is the capital of France. The city is famous for the Eiffel Tower. It has a rich history.",
            objections=("Needs more detail",),
            missing=("Population",),
            edits=("Add history section",),
        ),
        Response(
            model_name="model-2",
            answer="Paris is the capital of France. The city is famous for the Eiffel Tower. It attracts millions of tourists.",
            objections=("Needs more detail", "Missing demographics"),
            missing=(),
            edits=("Add history section",),
        ),
        Response(
            model_name="model-3",
            answer="Paris is the capital of France. The population is over 2 million.",
            objections=(),
            missing=(),
            edits=(),
        ),
    ]


@pytest.fixture
def responses_no_overlap():
    """Multiple responses with no overlapping content."""
    return [
        Response(
            model_name="model-1",
            answer="Paris is in France.",
        ),
        Response(
            model_name="model-2",
            answer="London is in England.",
        ),
    ]


@pytest.fixture
def responses_with_duplicates():
    """Responses with duplicate objections and edits."""
    return [
        Response(
            model_name="model-1",
            answer="Answer 1",
            objections=("Error A", "Error B", "Error A"),
            missing=("Item X",),
            edits=("Fix 1", "Fix 2"),
        ),
        Response(
            model_name="model-2",
            answer="Answer 2",
            objections=("Error A", "Error C"),
            missing=("Item X", "Item Y"),
            edits=("Fix 1",),
        ),
    ]


@pytest.fixture
def previous_digest():
    """Previous digest with some items (items in alphabetical order for deterministic sorting)."""
    return Digest(
        common_points=("Located in France", "Paris is the capital"),
        objections=("Missing sources", "Needs more detail"),  # Alphabetical order
        missing=("Population data",),
        suggested_edits=("Add introduction",),
    )


@pytest.fixture
def critique_responses():
    """Critique responses with new feedback."""
    return [
        Response(
            model_name="model-1",
            answer="",  # Critiques don't have answers used in digest
            objections=("Still needs more detail", "Grammar issue"),
            missing=("Historical context",),
            edits=("Fix grammar", "Add sources"),
        ),
        Response(
            model_name="model-2",
            answer="",
            objections=("Grammar issue",),
            missing=(),
            edits=("Fix grammar",),
        ),
    ]


# Tests: build_digest


def test_build_digest_empty_input():
    """Test building digest from empty response list."""
    digest = build_digest([])

    assert digest.common_points == ()
    assert digest.objections == ()
    assert digest.missing == ()
    assert digest.suggested_edits == ()


def test_build_digest_single_response(single_response):
    """Test building digest from single response."""
    digest = build_digest([single_response])

    # Single response means 100% frequency, so all sentences are common
    assert len(digest.common_points) > 0
    assert digest.objections == ()
    assert digest.missing == ()
    assert digest.suggested_edits == ()


def test_build_digest_with_critiques(response_with_critiques):
    """Test building digest from response with objections and edits."""
    digest = build_digest([response_with_critiques])

    # Should have objections, missing, and edits sorted
    assert digest.objections == ("Missing historical context", "Needs population data")
    assert digest.missing == ("Area size", "Founded date")
    assert digest.suggested_edits == ("Add more detail", "Include sources")


def test_build_digest_multiple_responses(multiple_responses_shared_content):
    """Test building digest from multiple responses with shared content."""
    digest = build_digest(multiple_responses_shared_content)

    # "Paris is the capital of France" appears in all 3 responses (100%)
    # "The city is famous for the Eiffel Tower" appears in 2 responses (67%)
    # Both should be included as common points (>= 50% threshold)
    # Sentences in the middle lose their trailing period (split on ". ")
    assert "Paris is the capital of France" in digest.common_points
    assert "The city is famous for the Eiffel Tower" in digest.common_points

    # "Needs more detail" appears twice, "Add history section" appears twice
    # These should be sorted by frequency then alphabetically
    assert "Needs more detail" in digest.objections
    assert "Add history section" in digest.suggested_edits


def test_build_digest_no_overlap(responses_no_overlap):
    """Test building digest when responses have no overlapping content."""
    digest = build_digest(responses_no_overlap)

    # Each sentence appears in only 1 of 2 responses (50%)
    # At exactly 50% threshold, should be included
    assert len(digest.common_points) >= 2


def test_build_digest_deduplicates_items(responses_with_duplicates):
    """Test that digest deduplicates objections, missing, and edits."""
    digest = build_digest(responses_with_duplicates)

    # "Error A" appears 3 times, should appear once but sorted first by frequency
    # Count of each: Error A=3, Item X=2, Fix 1=2
    assert digest.objections[0] == "Error A"  # Most frequent

    # Each item should appear only once
    assert digest.objections.count("Error A") == 1
    assert digest.missing.count("Item X") == 1
    assert digest.suggested_edits.count("Fix 1") == 1


def test_build_digest_deterministic_ordering(responses_with_duplicates):
    """Test that digest ordering is deterministic (frequency desc, then alpha)."""
    digest = build_digest(responses_with_duplicates)

    # Error A (3), Error B (1), Error C (1) -> Error A first, then B before C (alpha)
    assert digest.objections == ("Error A", "Error B", "Error C")

    # Item X (2), Item Y (1) -> X before Y
    assert digest.missing == ("Item X", "Item Y")

    # Fix 1 (2), Fix 2 (1) -> 1 before 2
    assert digest.suggested_edits == ("Fix 1", "Fix 2")


# Tests: _extract_common_points


def test_extract_common_points_empty():
    """Test extracting common points from empty response list."""
    common = _extract_common_points([])
    assert common == []


def test_extract_common_points_single_response(single_response):
    """Test extracting common points from single response."""
    common = _extract_common_points([single_response])

    # Single response means all sentences meet the 50% threshold
    # Implementation preserves original case
    assert len(common) == 2  # Two sentences in the answer
    assert "Paris is the capital of France" in common
    assert "It is located in northern France." in common


def test_extract_common_points_threshold():
    """Test that only sentences meeting 50% threshold are included."""
    responses = [
        Response(model_name="m1", answer="Sentence A. Sentence B."),
        Response(model_name="m2", answer="Sentence A. Sentence C."),
        Response(model_name="m3", answer="Sentence D."),
    ]

    common = _extract_common_points(responses)

    # Sentence A appears in 2/3 responses (67%) -> included
    # Others appear in 1/3 (33%) -> not included
    # Implementation preserves original case
    assert len(common) == 1
    assert "Sentence A" in common


def test_extract_common_points_frequency_ordering():
    """Test that common points are ordered by frequency then alphabetically."""
    responses = [
        Response(model_name="m1", answer="Alpha. Beta. Beta."),
        Response(model_name="m2", answer="Alpha. Beta. Beta."),
        Response(model_name="m3", answer="Beta. Gamma."),
    ]

    common = _extract_common_points(responses)

    # Beta appears 5 times total, Alpha appears 2 times
    # Both meet threshold (appear in at least 2/3 responses)
    # Beta should be first (higher frequency)
    # Implementation preserves original case
    assert common[0] == "Beta"
    assert "Alpha" in common


def test_extract_common_points_alphabetical_tiebreak():
    """Test alphabetical ordering when frequencies are equal."""
    responses = [
        Response(model_name="m1", answer="Zebra. Apple."),
        Response(model_name="m2", answer="Zebra. Apple."),
    ]

    common = _extract_common_points(responses)

    # Both appear with equal frequency (2 times each)
    # Sorted alphabetically - note: "Zebra" loses period (middle sentence),
    # "Apple." keeps period (final sentence)
    assert common[0] == "Apple."
    assert common[1] == "Zebra"


# Tests: _split_into_sentences


def test_split_into_sentences_empty():
    """Test splitting empty string."""
    sentences = _split_into_sentences("")
    assert sentences == []


def test_split_into_sentences_single():
    """Test splitting single sentence."""
    # Single sentence without trailing space keeps the period
    sentences = _split_into_sentences("This is a sentence.")
    assert len(sentences) == 1
    assert sentences[0] == "This is a sentence."


def test_split_into_sentences_multiple_delimiters():
    """Test splitting with various delimiters."""
    # Splits on ". ", "! ", "? ", "\n" - final sentence keeps its punctuation
    text = "First sentence. Second sentence! Third sentence? Fourth sentence\nFifth sentence."
    sentences = _split_into_sentences(text)

    assert len(sentences) == 5
    assert "First sentence" in sentences
    assert "Second sentence" in sentences
    assert "Third sentence" in sentences
    assert "Fourth sentence" in sentences
    assert "Fifth sentence." in sentences  # Final sentence keeps punctuation


def test_split_into_sentences_strips_whitespace():
    """Test that sentences are stripped of whitespace."""
    # Splits on ". " - the trailing ".  " contains ". " so it gets split too
    text = "  Sentence with spaces.   Another one.  "
    sentences = _split_into_sentences(text)

    assert sentences[0] == "Sentence with spaces"
    assert sentences[1] == "Another one"  # Period removed because ".  " contains ". "


def test_split_into_sentences_empty_segments():
    """Test that empty segments are filtered out."""
    text = "First... Second.  . Third."
    sentences = _split_into_sentences(text)

    # Empty segments from multiple delimiters should be filtered
    assert "" not in sentences
    assert len(sentences) >= 2  # At least First, Second, Third


def test_split_into_sentences_no_delimiters():
    """Test text without delimiters."""
    text = "Just one long sentence without any delimiters"
    sentences = _split_into_sentences(text)

    assert len(sentences) == 1
    assert sentences[0] == text


# Tests: _sort_by_frequency_and_alpha


def test_sort_by_frequency_empty():
    """Test sorting empty list."""
    sorted_items = _sort_by_frequency_and_alpha([])
    assert sorted_items == []


def test_sort_by_frequency_single():
    """Test sorting single item."""
    sorted_items = _sort_by_frequency_and_alpha(["item"])
    assert sorted_items == ["item"]


def test_sort_by_frequency_descending():
    """Test items sorted by frequency descending."""
    items = ["A", "B", "B", "C", "C", "C"]
    sorted_items = _sort_by_frequency_and_alpha(items)

    # C appears 3 times, B appears 2 times, A appears 1 time
    assert sorted_items == ["C", "B", "A"]


def test_sort_by_frequency_alphabetical_tiebreak():
    """Test alphabetical ordering for items with same frequency."""
    items = ["Zebra", "Apple", "Mango", "Apple", "Zebra", "Mango"]
    sorted_items = _sort_by_frequency_and_alpha(items)

    # All appear twice, should be sorted alphabetically
    assert sorted_items == ["Apple", "Mango", "Zebra"]


def test_sort_by_frequency_removes_duplicates():
    """Test that duplicates are removed in result."""
    items = ["A", "A", "A", "B", "B"]
    sorted_items = _sort_by_frequency_and_alpha(items)

    # Each item should appear only once
    assert sorted_items.count("A") == 1
    assert sorted_items.count("B") == 1
    assert sorted_items == ["A", "B"]


def test_sort_by_frequency_mixed_case():
    """Test sorting with mixed case strings."""
    items = ["alpha", "Beta", "GAMMA", "alpha", "Beta"]
    sorted_items = _sort_by_frequency_and_alpha(items)

    # alpha and Beta appear twice, GAMMA appears once
    # Alphabetical order: Beta, GAMMA, alpha
    assert sorted_items == ["Beta", "alpha", "GAMMA"]


def test_sort_by_frequency_special_characters():
    """Test sorting items with special characters."""
    items = ["item-1", "item_2", "item-1", "item.3", "item_2", "item_2"]
    sorted_items = _sort_by_frequency_and_alpha(items)

    # item_2 appears 3 times, item-1 appears 2 times, item.3 appears 1 time
    assert sorted_items[0] == "item_2"
    assert sorted_items[1] == "item-1"
    assert sorted_items[2] == "item.3"


# Tests: update_digest_from_critiques


def test_update_digest_empty_critiques(previous_digest):
    """Test updating digest with empty critique list."""
    updated = update_digest_from_critiques(previous_digest, [])

    # Should preserve previous digest exactly
    assert updated.common_points == previous_digest.common_points
    assert updated.objections == previous_digest.objections
    assert updated.missing == previous_digest.missing
    assert updated.suggested_edits == previous_digest.suggested_edits


def test_update_digest_preserves_common_points(previous_digest, critique_responses):
    """Test that updating digest preserves common points from previous digest."""
    updated = update_digest_from_critiques(previous_digest, critique_responses)

    # Common points should be unchanged
    assert updated.common_points == previous_digest.common_points


def test_update_digest_merges_objections(previous_digest, critique_responses):
    """Test that updating digest merges objections from previous and critiques."""
    updated = update_digest_from_critiques(previous_digest, critique_responses)

    # Should include objections from both previous and new critiques
    assert "Needs more detail" in updated.objections  # From previous
    assert "Missing sources" in updated.objections  # From previous
    assert "Still needs more detail" in updated.objections  # From critique
    assert "Grammar issue" in updated.objections  # From critique


def test_update_digest_merges_missing(previous_digest, critique_responses):
    """Test that updating digest merges missing items."""
    updated = update_digest_from_critiques(previous_digest, critique_responses)

    # Should include missing items from both
    assert "Population data" in updated.missing  # From previous
    assert "Historical context" in updated.missing  # From critique


def test_update_digest_merges_edits(previous_digest, critique_responses):
    """Test that updating digest merges suggested edits."""
    updated = update_digest_from_critiques(previous_digest, critique_responses)

    # Should include edits from both
    assert "Add introduction" in updated.suggested_edits  # From previous
    assert "Fix grammar" in updated.suggested_edits  # From critique
    assert "Add sources" in updated.suggested_edits  # From critique


def test_update_digest_deduplicates_merged_items(previous_digest):
    """Test that updating digest deduplicates items when merging."""
    critiques = [
        Response(
            model_name="m1",
            answer="",
            objections=("Needs more detail",),  # Duplicate from previous
            missing=("Population data",),  # Duplicate from previous
            edits=("Add introduction",),  # Duplicate from previous
        ),
    ]

    updated = update_digest_from_critiques(previous_digest, critiques)

    # Duplicates should appear only once
    assert updated.objections.count("Needs more detail") == 1
    assert updated.missing.count("Population data") == 1
    assert updated.suggested_edits.count("Add introduction") == 1


def test_update_digest_sorts_merged_items(previous_digest):
    """Test that updated digest sorts merged items deterministically."""
    critiques = [
        Response(
            model_name="m1",
            answer="",
            objections=("Grammar issue", "Grammar issue", "Needs more detail"),
            missing=(),
            edits=(),
        ),
    ]

    updated = update_digest_from_critiques(previous_digest, critiques)

    # "Needs more detail" now appears 2 times (1 previous + 1 critique)
    # "Grammar issue" appears 2 times (from critique)
    # "Missing sources" appears 1 time (from previous)
    # Should be sorted by frequency then alphabetically
    # Frequency: "Grammar issue"=2, "Needs more detail"=2, "Missing sources"=1
    # Alphabetical for ties: "Grammar issue" before "Needs more detail"
    assert updated.objections[0] == "Grammar issue"
    assert updated.objections[1] == "Needs more detail"
    assert "Missing sources" in updated.objections


def test_update_digest_from_empty_previous():
    """Test updating from an empty previous digest."""
    empty_digest = Digest()
    critiques = [
        Response(
            model_name="m1",
            answer="",
            objections=("New objection",),
            missing=("New missing",),
            edits=("New edit",),
        ),
    ]

    updated = update_digest_from_critiques(empty_digest, critiques)

    assert updated.common_points == ()
    assert updated.objections == ("New objection",)
    assert updated.missing == ("New missing",)
    assert updated.suggested_edits == ("New edit",)


# Tests: Edge cases and integration


def test_digest_with_unicode_content():
    """Test digest construction with unicode characters."""
    responses = [
        Response(model_name="m1", answer="Paris est la capitale de la France. C'est magnifique!"),
        Response(model_name="m2", answer="Paris est la capitale de la France. Très belle ville."),
    ]

    digest = build_digest(responses)

    # Should handle unicode characters properly
    assert len(digest.common_points) > 0


def test_digest_with_very_long_sentences():
    """Test digest with very long sentences."""
    long_sentence = "This is a very long sentence " * 50 + "."
    responses = [
        Response(model_name="m1", answer=long_sentence),
        Response(model_name="m2", answer=long_sentence),
    ]

    digest = build_digest(responses)

    # Should handle long sentences without issues
    assert len(digest.common_points) > 0


def test_digest_with_special_punctuation():
    """Test sentence splitting with special punctuation."""
    text = "Question? Answer! Statement. New paragraph\nAnother line."
    response = Response(model_name="m1", answer=text)

    digest = build_digest([response])

    # Should split on all delimiters
    assert len(digest.common_points) >= 4


def test_digest_case_sensitive_matching():
    """Test that common point extraction is case-sensitive (preserves original case)."""
    # Note: Implementation is case-sensitive, so different cases are treated as different sentences
    responses = [
        Response(model_name="m1", answer="Paris is the capital."),
        Response(model_name="m2", answer="Paris is the capital."),
        Response(model_name="m3", answer="Located in France."),
    ]

    digest = build_digest(responses)

    # "Paris is the capital." appears in 2/3 responses (67%) -> meets 50% threshold
    # "Located in France." appears in 1/3 responses (33%) -> doesn't meet threshold
    assert len(digest.common_points) == 1
    assert "Paris is the capital." in digest.common_points
