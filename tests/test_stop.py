"""Tests for stop conditions and change-threshold logic."""

from __future__ import annotations

import pytest

from aicx.consensus.stop import (
    check_below_change_threshold,
    check_consensus_reached,
    check_max_rounds_reached,
    check_no_changes_proposed,
    compute_change_ratio,
    should_stop,
)
from aicx.types import ModelConfig, Response, RunConfig


# Fixtures: ModelConfig and RunConfig


@pytest.fixture
def model_a():
    """First participant model."""
    return ModelConfig(name="model-a", provider="openai", model_id="gpt-4")


@pytest.fixture
def model_b():
    """Second participant model."""
    return ModelConfig(name="model-b", provider="anthropic", model_id="claude-3")


@pytest.fixture
def model_c():
    """Third participant model."""
    return ModelConfig(name="model-c", provider="google", model_id="gemini-1.5")


@pytest.fixture
def mediator():
    """Mediator model."""
    return ModelConfig(name="mediator", provider="openai", model_id="gpt-4o")


@pytest.fixture
def run_config_2_models(model_a, model_b, mediator):
    """Run config with 2 participant models."""
    return RunConfig(
        models=(model_a, model_b),
        mediator=mediator,
        max_rounds=3,
        approval_ratio=0.67,
        change_threshold=0.10,
    )


@pytest.fixture
def run_config_3_models(model_a, model_b, model_c, mediator):
    """Run config with 3 participant models."""
    return RunConfig(
        models=(model_a, model_b, model_c),
        mediator=mediator,
        max_rounds=3,
        approval_ratio=0.67,
        change_threshold=0.10,
    )


@pytest.fixture
def run_config_custom_threshold(model_a, model_b, mediator):
    """Run config with custom change threshold."""
    return RunConfig(
        models=(model_a, model_b),
        mediator=mediator,
        max_rounds=5,
        approval_ratio=0.67,
        change_threshold=0.20,
    )


# Fixtures: Response objects


@pytest.fixture
def response_approve_no_changes():
    """Response that approves with no changes."""
    return Response(
        model_name="model-a",
        answer="",
        approve=True,
        critical=False,
        objections=(),
        missing=(),
        edits=(),
    )


@pytest.fixture
def response_approve_with_objections():
    """Response that approves but has non-critical objections."""
    return Response(
        model_name="model-b",
        answer="",
        approve=True,
        critical=False,
        objections=("Minor wording issue",),
        missing=(),
        edits=(),
    )


@pytest.fixture
def response_reject_critical():
    """Response that rejects with critical objection."""
    return Response(
        model_name="model-c",
        answer="",
        approve=False,
        critical=True,
        objections=("Factually incorrect",),
        missing=(),
        edits=(),
    )


@pytest.fixture
def response_with_missing_items():
    """Response with missing items."""
    return Response(
        model_name="model-a",
        answer="",
        approve=False,
        critical=False,
        objections=(),
        missing=("Needs sources", "Add context"),
        edits=(),
    )


@pytest.fixture
def response_with_edits():
    """Response with suggested edits."""
    return Response(
        model_name="model-b",
        answer="",
        approve=False,
        critical=False,
        objections=(),
        missing=(),
        edits=("Rephrase introduction", "Fix grammar"),
    )


# Tests: check_consensus_reached


def test_consensus_reached_with_quorum_no_critical(run_config_2_models):
    """Test consensus is reached when quorum met and no critical objections."""
    # quorum = ceil(2 * 0.67) = 2
    assert check_consensus_reached(2, [], run_config_2_models) is True


def test_consensus_not_reached_below_quorum(run_config_2_models):
    """Test consensus not reached when below quorum."""
    # quorum = ceil(2 * 0.67) = 2, but only 1 approval
    assert check_consensus_reached(1, [], run_config_2_models) is False


def test_consensus_not_reached_with_critical_objections(run_config_2_models):
    """Test consensus not reached when critical objections exist."""
    # quorum = 2, meets threshold, but has critical objection
    assert check_consensus_reached(2, ["Critical error"], run_config_2_models) is False


def test_consensus_not_reached_multiple_critical(run_config_2_models):
    """Test consensus not reached with multiple critical objections."""
    critical_objs = ["Error 1", "Error 2", "Error 3"]
    assert check_consensus_reached(2, critical_objs, run_config_2_models) is False


def test_consensus_reached_with_3_models(run_config_3_models):
    """Test consensus with 3 models (quorum = 3)."""
    # quorum = ceil(3 * 0.67) = ceil(2.01) = 3
    assert check_consensus_reached(3, [], run_config_3_models) is True
    assert check_consensus_reached(2, [], run_config_3_models) is False
    assert check_consensus_reached(1, [], run_config_3_models) is False


def test_consensus_reached_exact_quorum(run_config_3_models):
    """Test consensus exactly at quorum threshold."""
    # quorum = ceil(3 * 0.67) = ceil(2.01) = 3
    assert check_consensus_reached(3, [], run_config_3_models) is True


def test_consensus_reached_above_quorum(run_config_3_models):
    """Test consensus with approvals above quorum."""
    # quorum = 2, but all 3 approve
    assert check_consensus_reached(3, [], run_config_3_models) is True


# Tests: check_max_rounds_reached


def test_max_rounds_not_reached(run_config_2_models):
    """Test max rounds not reached."""
    assert check_max_rounds_reached(1, run_config_2_models) is False
    assert check_max_rounds_reached(2, run_config_2_models) is False


def test_max_rounds_reached_exactly(run_config_2_models):
    """Test max rounds reached exactly."""
    assert check_max_rounds_reached(3, run_config_2_models) is True


def test_max_rounds_exceeded(run_config_2_models):
    """Test max rounds exceeded."""
    assert check_max_rounds_reached(4, run_config_2_models) is True
    assert check_max_rounds_reached(10, run_config_2_models) is True


def test_max_rounds_with_custom_config(run_config_custom_threshold):
    """Test max rounds with custom max_rounds setting."""
    # max_rounds = 5
    assert check_max_rounds_reached(4, run_config_custom_threshold) is False
    assert check_max_rounds_reached(5, run_config_custom_threshold) is True
    assert check_max_rounds_reached(6, run_config_custom_threshold) is True


# Tests: compute_change_ratio


def test_change_ratio_identical_texts():
    """Test change ratio for identical texts."""
    text = "The capital of France is Paris."
    assert compute_change_ratio(text, text) == 0.0


def test_change_ratio_empty_strings():
    """Test change ratio for empty strings."""
    assert compute_change_ratio("", "") == 0.0


def test_change_ratio_completely_different():
    """Test change ratio for completely different texts."""
    text1 = "The capital of France is Paris."
    text2 = "Tokyo is the capital of Japan."
    ratio = compute_change_ratio(text1, text2)
    # All tokens are different, so ratio should be high
    assert ratio > 0.8


def test_change_ratio_one_word_change():
    """Test change ratio with one word changed."""
    text1 = "The capital of France is Paris."
    text2 = "The capital of France is Lyon."
    ratio = compute_change_ratio(text1, text2)
    # Only "Paris" -> "Lyon" changed (1 out of 6 tokens)
    assert 0.1 < ratio < 0.3


def test_change_ratio_word_added():
    """Test change ratio with word added."""
    text1 = "The capital of France is Paris."
    text2 = "The capital city of France is Paris."
    ratio = compute_change_ratio(text1, text2)
    # One insertion: 1 edit out of 7 tokens in longer sequence
    assert 0.1 < ratio < 0.2


def test_change_ratio_word_removed():
    """Test change ratio with word removed."""
    text1 = "The capital city of France is Paris."
    text2 = "The capital of France is Paris."
    ratio = compute_change_ratio(text1, text2)
    # One deletion: 1 edit out of 7 tokens
    assert 0.1 < ratio < 0.2


def test_change_ratio_whitespace_normalized():
    """Test that whitespace is normalized (multiple spaces = single space)."""
    text1 = "The  capital   of    France"
    text2 = "The capital of France"
    # After tokenization, both become ["The", "capital", "of", "France"]
    assert compute_change_ratio(text1, text2) == 0.0


def test_change_ratio_empty_vs_nonempty():
    """Test change ratio between empty and non-empty text."""
    text1 = ""
    text2 = "The capital of France is Paris."
    ratio = compute_change_ratio(text1, text2)
    # All words must be inserted
    assert ratio == 1.0


def test_change_ratio_symmetric():
    """Test that change ratio is symmetric."""
    text1 = "The capital of France is Paris."
    text2 = "Paris is the capital of France."
    ratio1 = compute_change_ratio(text1, text2)
    ratio2 = compute_change_ratio(text2, text1)
    assert ratio1 == ratio2


def test_change_ratio_multiple_changes():
    """Test change ratio with multiple changes."""
    text1 = "Paris is the capital and largest city of France."
    text2 = "Lyon is a major city in France."
    ratio = compute_change_ratio(text1, text2)
    # Many words changed
    assert ratio > 0.5


def test_change_ratio_case_sensitive():
    """Test that change ratio is case-sensitive."""
    text1 = "The Capital Of France"
    text2 = "the capital of france"
    ratio = compute_change_ratio(text1, text2)
    # All tokens different due to case
    assert ratio > 0.5


# Tests: check_below_change_threshold


def test_below_threshold_no_change(run_config_2_models):
    """Test below threshold with identical texts."""
    text = "The capital of France is Paris."
    assert check_below_change_threshold(text, text, run_config_2_models) is True


def test_below_threshold_minor_change(run_config_2_models):
    """Test below threshold with minor change (< 10%)."""
    text1 = "The capital of France is Paris and it has a population of 2 million."
    text2 = "The capital of France is Paris and it has a population of 3 million."
    # Only one word changed (2 -> 3), should be < 10%
    ratio = compute_change_ratio(text1, text2)
    assert ratio < 0.10
    assert check_below_change_threshold(text1, text2, run_config_2_models) is True


def test_above_threshold_major_change(run_config_2_models):
    """Test above threshold with major change (>= 10%)."""
    text1 = "Paris is the capital."
    text2 = "Tokyo is the capital city of Japan."
    # Most words changed, should be >= 10%
    assert check_below_change_threshold(text1, text2, run_config_2_models) is False


def test_below_threshold_with_custom_threshold(run_config_custom_threshold):
    """Test below threshold with custom threshold (20%)."""
    text1 = "The capital of France is Paris."
    text2 = "The capital of Germany is Berlin."
    # "France" -> "Germany", "Paris" -> "Berlin" (2/6 = 33%)
    ratio = compute_change_ratio(text1, text2)
    # With 10% threshold, this would be above
    assert ratio > 0.10
    # With 20% threshold, this should still be above (33% > 20%)
    assert check_below_change_threshold(text1, text2, run_config_custom_threshold) is False


def test_exactly_at_threshold(run_config_2_models):
    """Test change exactly at threshold is not below threshold."""
    # Create a scenario where change is exactly 10%
    # With 10 words, changing 1 word = 10% change
    text1 = "one two three four five six seven eight nine ten"
    text2 = "CHANGED two three four five six seven eight nine ten"
    ratio = compute_change_ratio(text1, text2)
    # Should be exactly 0.1 (1/10)
    assert abs(ratio - 0.1) < 0.01
    # At threshold is NOT below threshold (< is strict)
    assert check_below_change_threshold(text1, text2, run_config_2_models) is False


# Tests: check_no_changes_proposed


def test_no_changes_proposed_all_approve(response_approve_no_changes):
    """Test no changes proposed when all approve with no feedback."""
    critiques = [response_approve_no_changes, response_approve_no_changes]
    assert check_no_changes_proposed(critiques) is True


def test_changes_proposed_with_objections(
    response_approve_no_changes, response_approve_with_objections
):
    """Test changes proposed when objections exist."""
    critiques = [response_approve_no_changes, response_approve_with_objections]
    assert check_no_changes_proposed(critiques) is False


def test_changes_proposed_with_missing(response_approve_no_changes, response_with_missing_items):
    """Test changes proposed when missing items exist."""
    critiques = [response_approve_no_changes, response_with_missing_items]
    assert check_no_changes_proposed(critiques) is False


def test_changes_proposed_with_edits(response_approve_no_changes, response_with_edits):
    """Test changes proposed when edits exist."""
    critiques = [response_approve_no_changes, response_with_edits]
    assert check_no_changes_proposed(critiques) is False


def test_changes_proposed_with_critical(response_approve_no_changes, response_reject_critical):
    """Test changes proposed when critical objections exist."""
    critiques = [response_approve_no_changes, response_reject_critical]
    assert check_no_changes_proposed(critiques) is False


def test_no_changes_empty_critiques():
    """Test no changes with empty critiques list."""
    assert check_no_changes_proposed([]) is True


def test_changes_proposed_multiple_types(
    response_with_missing_items, response_with_edits, response_reject_critical
):
    """Test changes proposed with multiple feedback types."""
    critiques = [response_with_missing_items, response_with_edits, response_reject_critical]
    assert check_no_changes_proposed(critiques) is False


# Tests: should_stop


def test_should_stop_consensus_reached(run_config_2_models, response_approve_no_changes):
    """Test should_stop returns True when consensus reached."""
    critiques = [response_approve_no_changes, response_approve_no_changes]
    should_stop_result, reason = should_stop(
        current_round=1,
        approval_count=2,
        critical_objections=[],
        previous_candidate=None,
        new_candidate="Paris is the capital of France.",
        critiques=critiques,
        config=run_config_2_models,
    )
    assert should_stop_result is True
    assert reason == "consensus_reached"


def test_should_stop_max_rounds(run_config_2_models, response_reject_critical):
    """Test should_stop returns True when max rounds reached."""
    critiques = [response_reject_critical]
    should_stop_result, reason = should_stop(
        current_round=3,
        approval_count=0,
        critical_objections=["Critical error"],
        previous_candidate="Old answer",
        new_candidate="New answer",
        critiques=critiques,
        config=run_config_2_models,
    )
    assert should_stop_result is True
    assert reason == "max_rounds_reached"


def test_should_stop_below_change_threshold(run_config_2_models, response_approve_no_changes):
    """Test should_stop returns True when change below threshold."""
    critiques = [response_approve_no_changes]
    previous = "The capital of France is Paris."
    new = "The capital of France is Paris."  # Identical
    should_stop_result, reason = should_stop(
        current_round=2,
        approval_count=1,  # Below quorum
        critical_objections=[],
        previous_candidate=previous,
        new_candidate=new,
        critiques=critiques,
        config=run_config_2_models,
    )
    assert should_stop_result is True
    assert reason == "below_change_threshold"


def test_should_stop_no_changes_proposed(run_config_2_models, response_approve_no_changes):
    """Test should_stop returns True when no changes proposed."""
    critiques = [response_approve_no_changes, response_approve_no_changes]
    should_stop_result, reason = should_stop(
        current_round=2,
        approval_count=1,  # Below quorum
        critical_objections=[],
        previous_candidate="Previous answer",
        new_candidate="Significantly different new answer with many changes",
        critiques=critiques,
        config=run_config_2_models,
    )
    assert should_stop_result is True
    assert reason == "no_changes_proposed"


def test_should_stop_continue_round_1(run_config_2_models, response_with_edits):
    """Test should_stop returns False in round 1 with no consensus."""
    critiques = [response_with_edits]  # Only 1 approval, need 2, has changes
    should_stop_result, reason = should_stop(
        current_round=1,
        approval_count=0,  # No consensus
        critical_objections=[],
        previous_candidate=None,  # Round 1 has no previous
        new_candidate="Paris is the capital.",
        critiques=critiques,
        config=run_config_2_models,
    )
    assert should_stop_result is False
    assert reason == ""


def test_should_stop_continue_with_changes(
    run_config_2_models, response_approve_no_changes, response_with_edits
):
    """Test should_stop returns False when changes proposed."""
    critiques = [response_approve_no_changes, response_with_edits]
    previous = "Previous answer."
    new = "Completely different new answer."
    should_stop_result, reason = should_stop(
        current_round=2,
        approval_count=1,  # Below quorum
        critical_objections=[],
        previous_candidate=previous,
        new_candidate=new,
        critiques=critiques,
        config=run_config_2_models,
    )
    assert should_stop_result is False
    assert reason == ""


def test_should_stop_priority_consensus_over_max_rounds(
    run_config_2_models, response_approve_no_changes
):
    """Test consensus check has priority over max rounds check."""
    critiques = [response_approve_no_changes, response_approve_no_changes]
    should_stop_result, reason = should_stop(
        current_round=3,  # At max rounds
        approval_count=2,  # But consensus reached
        critical_objections=[],
        previous_candidate="Previous",
        new_candidate="New",
        critiques=critiques,
        config=run_config_2_models,
    )
    # Should return consensus_reached, not max_rounds_reached
    assert should_stop_result is True
    assert reason == "consensus_reached"


def test_should_stop_priority_max_rounds_over_threshold(
    run_config_2_models, response_approve_no_changes
):
    """Test max rounds check has priority over change threshold check."""
    critiques = [response_approve_no_changes]
    previous = "The capital of France is Paris."
    new = "The capital of France is Paris."  # Identical
    should_stop_result, reason = should_stop(
        current_round=3,  # At max rounds
        approval_count=1,  # Below quorum
        critical_objections=[],
        previous_candidate=previous,
        new_candidate=new,
        critiques=critiques,
        config=run_config_2_models,
    )
    # Should return max_rounds_reached, not below_change_threshold
    assert should_stop_result is True
    assert reason == "max_rounds_reached"


def test_should_stop_priority_threshold_over_no_changes(
    run_config_2_models, response_approve_no_changes
):
    """Test change threshold check has priority over no changes check."""
    critiques = [response_approve_no_changes, response_approve_no_changes]
    previous = "The capital of France is Paris."
    new = "The capital of France is Paris."  # Identical
    should_stop_result, reason = should_stop(
        current_round=2,
        approval_count=1,  # Below quorum
        critical_objections=[],
        previous_candidate=previous,
        new_candidate=new,
        critiques=critiques,
        config=run_config_2_models,
    )
    # Should return below_change_threshold, not no_changes_proposed
    assert should_stop_result is True
    assert reason == "below_change_threshold"


def test_should_stop_no_previous_candidate_round_1(
    run_config_2_models, response_with_edits, response_with_missing_items
):
    """Test should_stop with no previous candidate (round 1 scenario)."""
    critiques = [response_with_edits, response_with_missing_items]
    should_stop_result, reason = should_stop(
        current_round=1,
        approval_count=0,
        critical_objections=[],
        previous_candidate=None,  # No previous in round 1
        new_candidate="First candidate answer.",
        critiques=critiques,
        config=run_config_2_models,
    )
    # Should continue (no consensus, not max rounds, changes proposed)
    assert should_stop_result is False
    assert reason == ""


def test_should_stop_with_critical_objections(run_config_2_models, response_reject_critical):
    """Test should_stop continues when critical objections present."""
    critiques = [response_reject_critical]
    should_stop_result, reason = should_stop(
        current_round=2,
        approval_count=2,  # Meets quorum
        critical_objections=["Factually incorrect"],  # But has critical
        previous_candidate="Previous",
        new_candidate="New",
        critiques=critiques,
        config=run_config_2_models,
    )
    # Should continue (consensus not reached due to critical objections)
    assert should_stop_result is False
    assert reason == ""


def test_should_stop_edge_case_large_change_above_threshold(
    run_config_2_models, response_with_edits
):
    """Test should_stop continues with large change above threshold."""
    critiques = [response_with_edits]
    previous = "Paris"
    new = "Tokyo is the capital of Japan with a large population."
    should_stop_result, reason = should_stop(
        current_round=2,
        approval_count=0,
        critical_objections=[],
        previous_candidate=previous,
        new_candidate=new,
        critiques=critiques,
        config=run_config_2_models,
    )
    # Should continue (large change, changes proposed)
    assert should_stop_result is False
    assert reason == ""


def test_should_stop_all_conditions_false(run_config_2_models, response_with_edits):
    """Test should_stop returns False when no stop conditions met."""
    critiques = [response_with_edits]
    should_stop_result, reason = should_stop(
        current_round=1,  # Not at max
        approval_count=0,  # No consensus
        critical_objections=[],
        previous_candidate=None,  # No previous to compare
        new_candidate="New candidate",
        critiques=critiques,  # Changes proposed
        config=run_config_2_models,
    )
    assert should_stop_result is False
    assert reason == ""
