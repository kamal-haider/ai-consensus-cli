"""Tests for quorum handling and zero-response detection."""

from __future__ import annotations

import pytest

from aicx.consensus.collection import FailedModel, collect_responses_with_failures
from aicx.consensus.errors import ZeroResponseError, check_round_responses
from aicx.types import ModelConfig, ProviderError, QuorumError, Response, RunConfig


@pytest.fixture
def sample_config() -> RunConfig:
    """Create a sample config with 3 participants (quorum = 2)."""
    return RunConfig(
        models=(
            ModelConfig(name="model-a", provider="test", model_id="test-1"),
            ModelConfig(name="model-b", provider="test", model_id="test-2"),
            ModelConfig(name="model-c", provider="test", model_id="test-3"),
        ),
        mediator=ModelConfig(name="mediator", provider="test", model_id="test-med"),
        max_rounds=3,
        approval_ratio=0.66,  # 3 * 0.66 = 1.98 -> ceil = 2
    )


class TestCheckRoundResponses:
    """Test check_round_responses validation."""

    def test_zero_responses_raises_zero_response_error(self, sample_config: RunConfig):
        """All models failed - should raise ZeroResponseError."""
        with pytest.raises(ZeroResponseError) as exc_info:
            check_round_responses([], sample_config, round_index=1)

        assert "All models failed in round 1" in str(exc_info.value)
        assert exc_info.value.round_index == 1

    def test_below_quorum_raises_quorum_error(self, sample_config: RunConfig):
        """Some responses but below quorum - should raise QuorumError."""
        # Only 1 response, but need 2 for quorum
        responses = [
            Response(model_name="model-a", answer="answer"),
        ]

        with pytest.raises(QuorumError) as exc_info:
            check_round_responses(responses, sample_config, round_index=1)

        assert exc_info.value.received == 1
        assert exc_info.value.required == 2
        assert "Insufficient responses in round 1" in str(exc_info.value)

    def test_quorum_met_passes(self, sample_config: RunConfig):
        """Quorum is met - should pass without error."""
        # 2 responses meets quorum threshold
        responses = [
            Response(model_name="model-a", answer="answer-a"),
            Response(model_name="model-b", answer="answer-b"),
        ]

        # Should not raise
        check_round_responses(responses, sample_config, round_index=1)

    def test_all_responses_passes(self, sample_config: RunConfig):
        """All models responded - should pass."""
        responses = [
            Response(model_name="model-a", answer="answer-a"),
            Response(model_name="model-b", answer="answer-b"),
            Response(model_name="model-c", answer="answer-c"),
        ]

        # Should not raise
        check_round_responses(responses, sample_config, round_index=1)

    def test_round_index_in_error_message(self, sample_config: RunConfig):
        """Error messages should include the round index."""
        with pytest.raises(ZeroResponseError) as exc_info:
            check_round_responses([], sample_config, round_index=3)

        assert "round 3" in str(exc_info.value)
        assert exc_info.value.round_index == 3


class TestCollectResponsesWithFailures:
    """Test collect_responses_with_failures helper."""

    def test_all_succeed(self, sample_config: RunConfig):
        """All models succeed - returns all responses, no failures."""

        def prompt_fn(model: ModelConfig) -> Response:
            return Response(model_name=model.name, answer=f"answer from {model.name}")

        responses, failed = collect_responses_with_failures(
            sample_config.models,
            prompt_fn,
            sample_config,
            round_index=1,
        )

        assert len(responses) == 3
        assert len(failed) == 0
        assert [r.model_name for r in responses] == ["model-a", "model-b", "model-c"]

    def test_all_fail(self, sample_config: RunConfig):
        """All models fail - returns no responses, all failures."""

        def prompt_fn(model: ModelConfig) -> Response:
            raise ProviderError(f"Failed: {model.name}", provider="test", code="timeout")

        responses, failed = collect_responses_with_failures(
            sample_config.models,
            prompt_fn,
            sample_config,
            round_index=1,
        )

        assert len(responses) == 0
        assert len(failed) == 3
        assert set(failed) == {"model-a", "model-b", "model-c"}

    def test_partial_failures(self, sample_config: RunConfig):
        """Some models succeed, some fail - returns both lists."""

        def prompt_fn(model: ModelConfig) -> Response:
            if model.name == "model-b":
                raise ProviderError(f"Failed: {model.name}", provider="test", code="rate_limit")
            return Response(model_name=model.name, answer=f"answer from {model.name}")

        responses, failed = collect_responses_with_failures(
            sample_config.models,
            prompt_fn,
            sample_config,
            round_index=2,
        )

        assert len(responses) == 2
        assert len(failed) == 1
        assert [r.model_name for r in responses] == ["model-a", "model-c"]
        assert failed == ("model-b",)

    def test_deterministic_ordering(self, sample_config: RunConfig):
        """Models are called in deterministic order (sorted by name)."""
        call_order = []

        def prompt_fn(model: ModelConfig) -> Response:
            call_order.append(model.name)
            return Response(model_name=model.name, answer="answer")

        collect_responses_with_failures(
            sample_config.models,
            prompt_fn,
            sample_config,
            round_index=1,
        )

        # Should be called in alphabetical order
        assert call_order == ["model-a", "model-b", "model-c"]

    def test_failed_models_tuple_immutable(self, sample_config: RunConfig):
        """Failed models list is returned as immutable tuple."""

        def prompt_fn(model: ModelConfig) -> Response:
            if model.name == "model-a":
                raise ProviderError("Failed", provider="test")
            return Response(model_name=model.name, answer="answer")

        _, failed = collect_responses_with_failures(
            sample_config.models,
            prompt_fn,
            sample_config,
            round_index=1,
        )

        assert isinstance(failed, tuple)


class TestFailedModelDataclass:
    """Test FailedModel dataclass."""

    def test_create_failed_model(self):
        """Can create FailedModel with required fields."""
        failed = FailedModel(name="model-x", error="Connection timeout")

        assert failed.name == "model-x"
        assert failed.error == "Connection timeout"
        assert failed.code is None

    def test_create_failed_model_with_code(self):
        """Can create FailedModel with error code."""
        failed = FailedModel(name="model-y", error="Rate limited", code="429")

        assert failed.name == "model-y"
        assert failed.error == "Rate limited"
        assert failed.code == "429"

    def test_failed_model_immutable(self):
        """FailedModel is frozen (immutable)."""
        failed = FailedModel(name="model-z", error="Error")

        with pytest.raises(AttributeError):
            failed.name = "other-model"  # type: ignore


class TestQuorumIntegration:
    """Integration tests for quorum handling in different scenarios."""

    def test_quorum_calculation(self):
        """Verify quorum is calculated correctly."""
        # 3 models, 66% approval -> ceil(3 * 0.66) = 2
        config = RunConfig(
            models=(
                ModelConfig(name="m1", provider="test", model_id="test-1"),
                ModelConfig(name="m2", provider="test", model_id="test-2"),
                ModelConfig(name="m3", provider="test", model_id="test-3"),
            ),
            mediator=ModelConfig(name="med", provider="test", model_id="test-med"),
            approval_ratio=0.66,  # 3 * 0.66 = 1.98 -> ceil = 2
        )
        assert config.quorum == 2

        # 4 models, 67% approval -> ceil(4 * 0.67) = ceil(2.68) = 3
        config = RunConfig(
            models=(
                ModelConfig(name="m1", provider="test", model_id="test-1"),
                ModelConfig(name="m2", provider="test", model_id="test-2"),
                ModelConfig(name="m3", provider="test", model_id="test-3"),
                ModelConfig(name="m4", provider="test", model_id="test-4"),
            ),
            mediator=ModelConfig(name="med", provider="test", model_id="test-med"),
            approval_ratio=0.67,
        )
        assert config.quorum == 3

    def test_zero_responses_different_from_quorum_error(self, sample_config: RunConfig):
        """ZeroResponseError is distinct from QuorumError."""
        # Zero responses
        with pytest.raises(ZeroResponseError):
            check_round_responses([], sample_config, round_index=1)

        # Below quorum but not zero
        with pytest.raises(QuorumError):
            check_round_responses(
                [Response(model_name="m1", answer="a")],
                sample_config,
                round_index=1,
            )

    def test_collect_and_check_zero_responses(self, sample_config: RunConfig):
        """Collect with all failures, then check raises ZeroResponseError."""

        def prompt_fn(model: ModelConfig) -> Response:
            raise ProviderError("All failed", provider="test")

        responses, failed = collect_responses_with_failures(
            sample_config.models,
            prompt_fn,
            sample_config,
            round_index=1,
        )

        assert len(responses) == 0
        assert len(failed) == 3

        with pytest.raises(ZeroResponseError):
            check_round_responses(responses, sample_config, round_index=1)

    def test_collect_and_check_below_quorum(self, sample_config: RunConfig):
        """Collect with partial failures, check raises QuorumError."""

        def prompt_fn(model: ModelConfig) -> Response:
            # Only model-a succeeds
            if model.name == "model-a":
                return Response(model_name=model.name, answer="answer")
            raise ProviderError("Failed", provider="test")

        responses, failed = collect_responses_with_failures(
            sample_config.models,
            prompt_fn,
            sample_config,
            round_index=1,
        )

        assert len(responses) == 1
        assert len(failed) == 2

        with pytest.raises(QuorumError):
            check_round_responses(responses, sample_config, round_index=1)

    def test_collect_and_check_quorum_met(self, sample_config: RunConfig):
        """Collect with enough successes, check passes."""

        def prompt_fn(model: ModelConfig) -> Response:
            # model-a and model-b succeed (meets quorum of 2)
            if model.name in ("model-a", "model-b"):
                return Response(model_name=model.name, answer="answer")
            raise ProviderError("Failed", provider="test")

        responses, failed = collect_responses_with_failures(
            sample_config.models,
            prompt_fn,
            sample_config,
            round_index=1,
        )

        assert len(responses) == 2
        assert len(failed) == 1

        # Should not raise
        check_round_responses(responses, sample_config, round_index=1)
