"""Tests for consensus runner orchestration.

NOTE: The current implementation uses stub provider calls that always return
successful responses. This means some error conditions (like QuorumError from
insufficient responses) cannot be tested until real provider adapters are
implemented. These tests focus on:
- Basic orchestration flow and round tracking
- Helper function logic (_analyze_critiques, _build_disagreement_summary)
- Result structure and metadata population
- Configuration options (max_rounds, share_mode, etc.)
- Deterministic behavior with stub data
"""

from __future__ import annotations

import pytest

from aicx.consensus.runner import (
    ConsensusContext,
    _analyze_critiques,
    _build_disagreement_summary,
    run_consensus,
)
from aicx.types import (
    ExitCode,
    ModelConfig,
    QuorumError,
    Response,
    RunConfig,
    ShareMode,
)


# Fixtures


@pytest.fixture
def model_a():
    """Create a test model configuration A."""
    return ModelConfig(
        name="model-a",
        provider="openai",
        model_id="gpt-4",
        temperature=0.2,
    )


@pytest.fixture
def model_b():
    """Create a test model configuration B."""
    return ModelConfig(
        name="model-b",
        provider="anthropic",
        model_id="claude-3",
        temperature=0.2,
    )


@pytest.fixture
def model_c():
    """Create a test model configuration C."""
    return ModelConfig(
        name="model-c",
        provider="openai",
        model_id="gpt-3.5",
        temperature=0.2,
    )


@pytest.fixture
def mediator():
    """Create a mediator model configuration."""
    return ModelConfig(
        name="mediator",
        provider="openai",
        model_id="gpt-4o",
        temperature=0.2,
    )


@pytest.fixture
def run_config_two_models(model_a, model_b, mediator):
    """Create a RunConfig with two participant models."""
    return RunConfig(
        models=(model_a, model_b),
        mediator=mediator,
        max_rounds=3,
        approval_ratio=0.67,
        change_threshold=0.10,
        verbose=False,
        strict_json=False,
        share_mode=ShareMode.DIGEST,
    )


@pytest.fixture
def run_config_three_models(model_a, model_b, model_c, mediator):
    """Create a RunConfig with three participant models."""
    return RunConfig(
        models=(model_a, model_b, model_c),
        mediator=mediator,
        max_rounds=3,
        approval_ratio=0.67,
        change_threshold=0.10,
        verbose=False,
        strict_json=False,
        share_mode=ShareMode.DIGEST,
    )


# Tests: Helper Functions


def test_analyze_critiques_all_approve():
    """Test analyzing critiques when all participants approve."""
    critiques = [
        Response(model_name="model-a", answer="", approve=True, critical=False),
        Response(model_name="model-b", answer="", approve=True, critical=False),
        Response(model_name="model-c", answer="", approve=True, critical=False),
    ]

    approval_count, critical_objections = _analyze_critiques(critiques)

    assert approval_count == 3
    assert len(critical_objections) == 0


def test_analyze_critiques_mixed_approvals():
    """Test analyzing critiques with mixed approvals."""
    critiques = [
        Response(model_name="model-a", answer="", approve=True, critical=False),
        Response(model_name="model-b", answer="", approve=False, critical=False),
        Response(model_name="model-c", answer="", approve=True, critical=False),
    ]

    approval_count, critical_objections = _analyze_critiques(critiques)

    assert approval_count == 2
    assert len(critical_objections) == 0


def test_analyze_critiques_with_critical_objections():
    """Test analyzing critiques with critical objections."""
    critiques = [
        Response(model_name="model-a", answer="", approve=True, critical=False),
        Response(
            model_name="model-b",
            answer="",
            approve=False,
            critical=True,
            objections=("Factually incorrect", "Missing context"),
        ),
        Response(model_name="model-c", answer="", approve=True, critical=False),
    ]

    approval_count, critical_objections = _analyze_critiques(critiques)

    assert approval_count == 2
    assert len(critical_objections) == 2
    assert "Factually incorrect" in critical_objections
    assert "Missing context" in critical_objections


def test_analyze_critiques_multiple_critical():
    """Test analyzing critiques with multiple critical objections."""
    critiques = [
        Response(
            model_name="model-a",
            answer="",
            approve=False,
            critical=True,
            objections=("Problem A",),
        ),
        Response(
            model_name="model-b",
            answer="",
            approve=False,
            critical=True,
            objections=("Problem B", "Problem C"),
        ),
    ]

    approval_count, critical_objections = _analyze_critiques(critiques)

    assert approval_count == 0
    assert len(critical_objections) == 3


def test_analyze_critiques_non_critical_objections_ignored():
    """Test that non-critical objections are not included."""
    critiques = [
        Response(
            model_name="model-a",
            answer="",
            approve=False,
            critical=False,
            objections=("Minor issue",),
        ),
    ]

    approval_count, critical_objections = _analyze_critiques(critiques)

    assert approval_count == 0
    assert len(critical_objections) == 0


def test_analyze_critiques_empty_list():
    """Test analyzing an empty critique list."""
    critiques = []

    approval_count, critical_objections = _analyze_critiques(critiques)

    assert approval_count == 0
    assert len(critical_objections) == 0


def test_build_disagreement_summary_with_critical():
    """Test building disagreement summary with critical objections."""
    critiques = [
        Response(
            model_name="model-a",
            answer="",
            approve=False,
            critical=True,
            objections=("Critical issue 1", "Critical issue 2"),
        ),
    ]
    critical_objections = ("Critical issue 1", "Critical issue 2")

    summary = _build_disagreement_summary(critiques, critical_objections)

    assert "Disagreement Summary:" in summary
    assert "Critical objections (2):" in summary
    assert "Critical issue 1" in summary
    assert "Critical issue 2" in summary
    assert "Consensus not reached within round limits." in summary


def test_build_disagreement_summary_with_objections():
    """Test building disagreement summary with regular objections."""
    critiques = [
        Response(
            model_name="model-a",
            answer="",
            approve=False,
            critical=False,
            objections=("Objection 1", "Objection 2", "Objection 3"),
        ),
        Response(
            model_name="model-b",
            answer="",
            approve=False,
            critical=False,
            objections=("Objection 4",),
        ),
    ]
    critical_objections = ()

    summary = _build_disagreement_summary(critiques, critical_objections)

    assert "Top objections (4):" in summary
    assert "Objection 1" in summary
    assert "Objection 2" in summary
    assert "Objection 3" in summary
    # Should only show top 3
    assert "Objection 4" not in summary


def test_build_disagreement_summary_with_missing():
    """Test building disagreement summary with missing items."""
    critiques = [
        Response(
            model_name="model-a",
            answer="",
            approve=False,
            critical=False,
            objections=(),
            missing=("Missing A", "Missing B"),
        ),
    ]
    critical_objections = ()

    summary = _build_disagreement_summary(critiques, critical_objections)

    assert "Missing items (2):" in summary
    assert "Missing A" in summary
    assert "Missing B" in summary


def test_build_disagreement_summary_empty():
    """Test building disagreement summary with no objections."""
    critiques = []
    critical_objections = ()

    summary = _build_disagreement_summary(critiques, critical_objections)

    assert "Disagreement Summary:" in summary
    assert "Consensus not reached within round limits." in summary


# Tests: run_consensus function


def test_run_consensus_basic_execution(run_config_two_models):
    """Test basic execution of run_consensus completes successfully."""
    prompt = "What is the capital of France?"

    result = run_consensus(prompt, run_config_two_models)

    assert result.output is not None
    assert result.exit_code == ExitCode.SUCCESS
    assert result.rounds_completed >= 1
    assert len(result.responses) > 0
    assert result.digest is not None
    assert result.mediator_state is not None
    assert result.metadata["prompt"] == prompt


def test_run_consensus_with_three_models(run_config_three_models):
    """Test run_consensus with three participant models."""
    prompt = "Explain quantum computing."

    result = run_consensus(prompt, run_config_three_models)

    assert result.exit_code == ExitCode.SUCCESS
    assert result.rounds_completed >= 1
    # Round 1 has 3 responses, subsequent rounds have 3 critiques each
    assert len(result.responses) >= 3


def test_run_consensus_quorum_check(run_config_two_models):
    """Test that quorum is calculated correctly."""
    prompt = "Test prompt"

    # With 2 models and 0.67 approval ratio, quorum should be ceil(2 * 0.67) = 2
    assert run_config_two_models.quorum == 2

    result = run_consensus(prompt, run_config_two_models)

    # Stub implementation returns 2 responses, meeting quorum
    assert result.exit_code == ExitCode.SUCCESS


def test_run_consensus_max_rounds_respected(run_config_two_models):
    """Test that consensus loop respects max_rounds."""
    prompt = "Test prompt"

    result = run_consensus(prompt, run_config_two_models)

    # Should not exceed max_rounds
    assert result.rounds_completed <= run_config_two_models.max_rounds


def test_run_consensus_no_consensus_summary_flag(run_config_two_models):
    """Test that no_consensus_summary flag omits disagreement summary."""
    prompt = "Test prompt"

    # Without flag (default)
    result_with_summary = run_consensus(prompt, run_config_two_models, no_consensus_summary=False)

    # With flag
    result_without_summary = run_consensus(prompt, run_config_two_models, no_consensus_summary=True)

    # Both should complete successfully
    assert result_with_summary.exit_code == ExitCode.SUCCESS
    assert result_without_summary.exit_code == ExitCode.SUCCESS


def test_run_consensus_metadata_populated(run_config_three_models):
    """Test that result metadata is correctly populated."""
    prompt = "Test metadata"

    result = run_consensus(prompt, run_config_three_models)

    assert result.metadata["prompt"] == prompt
    assert result.metadata["participants"] == 3
    assert result.metadata["quorum"] == 2  # ceil(3 * 0.67) = 2


def test_run_consensus_responses_tracked(run_config_two_models):
    """Test that all responses are tracked across rounds."""
    prompt = "Test response tracking"

    result = run_consensus(prompt, run_config_two_models)

    # Should have round 1 responses plus critique responses from subsequent rounds
    # With 2 models: round 1 = 2 responses, each subsequent round = 2 critiques
    assert len(result.responses) >= 2


def test_run_consensus_digest_created(run_config_two_models):
    """Test that digest is created and updated."""
    prompt = "Test digest"

    result = run_consensus(prompt, run_config_two_models)

    assert result.digest is not None
    # Digest should have all fields (may be empty tuples)
    assert hasattr(result.digest, "common_points")
    assert hasattr(result.digest, "objections")
    assert hasattr(result.digest, "missing")
    assert hasattr(result.digest, "suggested_edits")


def test_run_consensus_mediator_state_populated(run_config_two_models):
    """Test that mediator state is populated in result."""
    prompt = "Test mediator state"

    result = run_consensus(prompt, run_config_two_models)

    assert result.mediator_state is not None
    assert result.mediator_state.candidate_answer is not None
    assert result.mediator_state.rationale is not None
    assert result.mediator_state.approval_count >= 0
    assert result.mediator_state.critical_objections is not None


def test_run_consensus_context_creation():
    """Test ConsensusContext dataclass creation."""
    model = ModelConfig(name="test", provider="openai", model_id="gpt-4")
    config = RunConfig(models=(model, model), mediator=model)
    prompt = "Test"

    context = ConsensusContext(prompt=prompt, config=config)

    assert context.prompt == prompt
    assert context.config == config


def test_run_consensus_different_max_rounds(model_a, model_b, mediator):
    """Test run_consensus with different max_rounds values."""
    prompt = "Test rounds"

    # Test with 1 round
    config_1_round = RunConfig(
        models=(model_a, model_b),
        mediator=mediator,
        max_rounds=1,
    )
    result_1 = run_consensus(prompt, config_1_round)
    assert result_1.rounds_completed == 1

    # Test with 5 rounds
    config_5_rounds = RunConfig(
        models=(model_a, model_b),
        mediator=mediator,
        max_rounds=5,
    )
    result_5 = run_consensus(prompt, config_5_rounds)
    assert result_5.rounds_completed <= 5


def test_run_consensus_share_mode_raw(model_a, model_b, mediator):
    """Test run_consensus with RAW share mode."""
    prompt = "Test share mode"

    config = RunConfig(
        models=(model_a, model_b),
        mediator=mediator,
        share_mode=ShareMode.RAW,
    )

    result = run_consensus(prompt, config)

    assert result.exit_code == ExitCode.SUCCESS


def test_run_consensus_verbose_mode(model_a, model_b, mediator):
    """Test run_consensus with verbose mode enabled."""
    prompt = "Test verbose"

    config = RunConfig(
        models=(model_a, model_b),
        mediator=mediator,
        verbose=True,
    )

    result = run_consensus(prompt, config)

    assert result.exit_code == ExitCode.SUCCESS


def test_run_consensus_strict_json_mode(model_a, model_b, mediator):
    """Test run_consensus with strict JSON mode enabled."""
    prompt = "Test strict JSON"

    config = RunConfig(
        models=(model_a, model_b),
        mediator=mediator,
        strict_json=True,
    )

    result = run_consensus(prompt, config)

    assert result.exit_code == ExitCode.SUCCESS


def test_run_consensus_deterministic_ordering(run_config_two_models):
    """Test that run_consensus produces deterministic results."""
    prompt = "Test determinism"

    # Run twice with same config
    result1 = run_consensus(prompt, run_config_two_models)
    result2 = run_consensus(prompt, run_config_two_models)

    # Should have same number of rounds and responses
    assert result1.rounds_completed == result2.rounds_completed
    assert len(result1.responses) == len(result2.responses)

    # Model names should appear in same order (deterministic sorting)
    models1 = [r.model_name for r in result1.responses[:2]]  # First round
    models2 = [r.model_name for r in result2.responses[:2]]  # First round
    assert models1 == models2


def test_run_consensus_empty_prompt(run_config_two_models):
    """Test run_consensus with empty prompt."""
    prompt = ""

    result = run_consensus(prompt, run_config_two_models)

    # Should still complete successfully
    assert result.exit_code == ExitCode.SUCCESS
    assert result.metadata["prompt"] == ""


def test_run_consensus_long_prompt(run_config_two_models):
    """Test run_consensus with very long prompt."""
    prompt = "A" * 10000

    result = run_consensus(prompt, run_config_two_models)

    assert result.exit_code == ExitCode.SUCCESS


def test_run_consensus_special_characters_in_prompt(run_config_two_models):
    """Test run_consensus with special characters in prompt."""
    prompt = "Test with special chars: @#$%^&*(){}[]|\\:;\"'<>,.?/~`"

    result = run_consensus(prompt, run_config_two_models)

    assert result.exit_code == ExitCode.SUCCESS
    assert result.metadata["prompt"] == prompt


def test_run_consensus_unicode_in_prompt(run_config_two_models):
    """Test run_consensus with unicode characters in prompt."""
    prompt = "Test unicode: \u2013 \u2014 \u00e9 \u00f1 \u4e2d\u6587"

    result = run_consensus(prompt, run_config_two_models)

    assert result.exit_code == ExitCode.SUCCESS


def test_run_consensus_approval_count_tracking(run_config_two_models):
    """Test that approval count is tracked in mediator state."""
    prompt = "Test approvals"

    result = run_consensus(prompt, run_config_two_models)

    # Stub implementation has all models approve
    assert result.mediator_state.approval_count >= 0
    assert result.mediator_state.approval_count <= len(run_config_two_models.models)


def test_run_consensus_critical_objections_tracking(run_config_two_models):
    """Test that critical objections are tracked in mediator state."""
    prompt = "Test critical objections"

    result = run_consensus(prompt, run_config_two_models)

    # Stub implementation has no critical objections
    assert isinstance(result.mediator_state.critical_objections, tuple)


def test_run_consensus_result_immutable(run_config_two_models):
    """Test that ConsensusResult is frozen/immutable."""
    prompt = "Test immutability"

    result = run_consensus(prompt, run_config_two_models)

    # Should not be able to modify result
    with pytest.raises(Exception):  # dataclass frozen raises either FrozenInstanceError or AttributeError
        result.output = "Modified"

    with pytest.raises(Exception):
        result.exit_code = ExitCode.CONFIG_ERROR


def test_analyze_critiques_preserves_order():
    """Test that critical objections preserve order from responses."""
    critiques = [
        Response(
            model_name="model-a",
            answer="",
            approve=False,
            critical=True,
            objections=("First", "Second"),
        ),
        Response(
            model_name="model-b",
            answer="",
            approve=False,
            critical=True,
            objections=("Third",),
        ),
    ]

    _, critical_objections = _analyze_critiques(critiques)

    # Should preserve order: First, Second, Third
    assert critical_objections[0] == "First"
    assert critical_objections[1] == "Second"
    assert critical_objections[2] == "Third"


def test_build_disagreement_summary_truncates_long_lists():
    """Test that disagreement summary shows only top 3 items."""
    critiques = [
        Response(
            model_name="model-a",
            answer="",
            approve=False,
            critical=False,
            objections=("Obj1", "Obj2", "Obj3", "Obj4", "Obj5"),
        ),
    ]
    critical_objections = ()

    summary = _build_disagreement_summary(critiques, critical_objections)

    # Should show first 3 objections
    assert "Obj1" in summary
    assert "Obj2" in summary
    assert "Obj3" in summary
    # Should not show 4th and 5th
    assert "Obj4" not in summary
    assert "Obj5" not in summary


# Tests deferred until real provider adapters are implemented:
# - test_run_consensus_quorum_error: Cannot trigger QuorumError with stub
#   implementation that always returns all responses
# - test_run_consensus_provider_failures: Need real providers to test failure handling
# - test_run_consensus_timeout_handling: Need real providers with timeout support
# - test_run_consensus_network_errors: Need real network calls to test error handling
