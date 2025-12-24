"""Tests for context budget enforcement."""

from __future__ import annotations

import pytest

from aicx.context.budget import ContextBudget, track_usage, would_exceed_budget
from aicx.context.tokens import (
    count_prompt_tokens,
    count_response_tokens,
    estimate_tokens,
)
from aicx.context.truncation import build_truncated_digest, truncate_oldest_rounds
from aicx.types import Digest, PromptRequest, Response, Role


class TestTokenEstimation:
    """Test token estimation functions."""

    def test_estimate_tokens_empty(self):
        """Empty text should return 0 tokens."""
        assert estimate_tokens("") == 0

    def test_estimate_tokens_short(self):
        """Short text should estimate correctly."""
        # "test" is 4 chars, should be 1 token (4/4 = 1)
        assert estimate_tokens("test") == 1

    def test_estimate_tokens_medium(self):
        """Medium text should estimate correctly."""
        # 100 chars should be 25 tokens (100/4 = 25)
        text = "a" * 100
        assert estimate_tokens(text) == 25

    def test_estimate_tokens_rounds_up(self):
        """Token estimation should round up."""
        # 5 chars should be 2 tokens (5/4 = 1.25, rounds up to 2)
        assert estimate_tokens("hello") == 2

    def test_estimate_tokens_large(self):
        """Large text should estimate correctly."""
        # 1000 chars should be 250 tokens
        text = "a" * 1000
        assert estimate_tokens(text) == 250

    def test_count_prompt_tokens_minimal(self):
        """Minimal prompt request should count tokens correctly."""
        request = PromptRequest(
            user_prompt="What is 2+2?",
            system_prompt="You are a helpful assistant.",
            round_index=0,
            role=Role.PARTICIPANT,
        )
        tokens = count_prompt_tokens(request)
        # Should count both prompts
        expected = estimate_tokens("What is 2+2?") + estimate_tokens("You are a helpful assistant.")
        assert tokens == expected

    def test_count_prompt_tokens_with_digest(self):
        """Prompt with digest should count all components."""
        digest = Digest(
            common_points=("Point 1", "Point 2"),
            objections=("Objection 1",),
            missing=(),
            suggested_edits=(),
        )
        request = PromptRequest(
            user_prompt="prompt",
            system_prompt="system",
            round_index=1,
            role=Role.PARTICIPANT,
            input_digest=digest,
        )
        tokens = count_prompt_tokens(request)
        # Should count prompts + digest
        assert tokens > estimate_tokens("prompt") + estimate_tokens("system")

    def test_count_prompt_tokens_with_candidate(self):
        """Prompt with candidate answer should count it."""
        request = PromptRequest(
            user_prompt="prompt",
            system_prompt="system",
            round_index=1,
            role=Role.PARTICIPANT,
            candidate_answer="This is the candidate answer.",
        )
        tokens = count_prompt_tokens(request)
        expected = (
            estimate_tokens("prompt")
            + estimate_tokens("system")
            + estimate_tokens("This is the candidate answer.")
        )
        assert tokens == expected

    def test_count_response_tokens_minimal(self):
        """Minimal response should count answer tokens."""
        response = Response(
            model_name="test-model",
            answer="This is an answer.",
        )
        tokens = count_response_tokens(response)
        assert tokens == estimate_tokens("This is an answer.")

    def test_count_response_tokens_with_critique(self):
        """Response with critique fields should count all components."""
        response = Response(
            model_name="test-model",
            answer="Answer text",
            approve=False,
            objections=("Objection 1", "Objection 2"),
            missing=("Missing item",),
            edits=("Edit suggestion",),
        )
        tokens = count_response_tokens(response)
        # Should count answer + all critique components
        expected = (
            estimate_tokens("Answer text")
            + estimate_tokens("Objection 1")
            + estimate_tokens("Objection 2")
            + estimate_tokens("Missing item")
            + estimate_tokens("Edit suggestion")
        )
        assert tokens == expected


class TestContextBudget:
    """Test context budget tracking."""

    def test_budget_creation(self):
        """Budget should be created with max_tokens."""
        budget = ContextBudget(max_tokens=1000)
        assert budget.max_tokens == 1000
        assert budget.used_tokens == 0
        assert budget.round_usage == ()

    def test_budget_validation_max_tokens(self):
        """Budget should validate max_tokens >= 1."""
        with pytest.raises(ValueError, match="max_tokens must be >= 1"):
            ContextBudget(max_tokens=0)

    def test_budget_validation_used_tokens(self):
        """Budget should validate used_tokens >= 0."""
        with pytest.raises(ValueError, match="used_tokens must be >= 0"):
            ContextBudget(max_tokens=1000, used_tokens=-1)

    def test_budget_validation_used_exceeds_max(self):
        """Budget should validate used_tokens <= max_tokens."""
        with pytest.raises(ValueError, match="used_tokens.*exceeds max_tokens"):
            ContextBudget(max_tokens=1000, used_tokens=1001)

    def test_track_usage_first_round(self):
        """Track usage for first round."""
        budget = ContextBudget(max_tokens=1000)
        new_budget = track_usage(budget, tokens=100, round_idx=0)

        assert new_budget.max_tokens == 1000
        assert new_budget.used_tokens == 100
        assert new_budget.round_usage == (100,)

    def test_track_usage_multiple_rounds(self):
        """Track usage across multiple rounds."""
        budget = ContextBudget(max_tokens=1000)

        budget = track_usage(budget, tokens=100, round_idx=0)
        budget = track_usage(budget, tokens=150, round_idx=1)
        budget = track_usage(budget, tokens=200, round_idx=2)

        assert budget.used_tokens == 450
        assert budget.round_usage == (100, 150, 200)

    def test_track_usage_same_round_accumulates(self):
        """Multiple tracking calls for same round should accumulate."""
        budget = ContextBudget(max_tokens=1000)

        budget = track_usage(budget, tokens=100, round_idx=0)
        budget = track_usage(budget, tokens=50, round_idx=0)

        assert budget.used_tokens == 150
        assert budget.round_usage == (150,)

    def test_track_usage_skip_rounds(self):
        """Tracking non-sequential rounds should work."""
        budget = ContextBudget(max_tokens=1000)

        budget = track_usage(budget, tokens=100, round_idx=0)
        budget = track_usage(budget, tokens=200, round_idx=2)  # Skip round 1

        assert budget.used_tokens == 300
        assert budget.round_usage == (100, 0, 200)

    def test_track_usage_negative_tokens(self):
        """Tracking negative tokens should raise error."""
        budget = ContextBudget(max_tokens=1000)
        with pytest.raises(ValueError, match="tokens must be >= 0"):
            track_usage(budget, tokens=-1, round_idx=0)

    def test_would_exceed_budget_no_usage(self):
        """Check budget exceeded with no prior usage."""
        budget = ContextBudget(max_tokens=1000)
        assert not would_exceed_budget(budget, 500)
        assert not would_exceed_budget(budget, 1000)
        assert would_exceed_budget(budget, 1001)

    def test_would_exceed_budget_with_usage(self):
        """Check budget exceeded with prior usage."""
        budget = ContextBudget(max_tokens=1000, used_tokens=600)
        assert not would_exceed_budget(budget, 400)
        assert would_exceed_budget(budget, 401)

    def test_would_exceed_budget_exact_limit(self):
        """Using exactly the remaining budget should not exceed."""
        budget = ContextBudget(max_tokens=1000, used_tokens=600)
        assert not would_exceed_budget(budget, 400)

    def test_would_exceed_budget_negative_tokens(self):
        """Checking with negative tokens should raise error."""
        budget = ContextBudget(max_tokens=1000)
        with pytest.raises(ValueError, match="additional_tokens must be >= 0"):
            would_exceed_budget(budget, -1)


class TestTruncation:
    """Test round truncation logic."""

    def test_truncate_oldest_rounds_empty(self):
        """Truncating empty responses should return empty."""
        result = truncate_oldest_rounds(
            responses=(),
            round_indices=(),
            budget=ContextBudget(max_tokens=1000),
            target_tokens=500,
        )
        assert result == ()

    def test_truncate_oldest_rounds_no_truncation_needed(self):
        """If within budget, no truncation should occur."""
        responses = (
            Response(model_name="m1", answer="Short answer"),
            Response(model_name="m2", answer="Another short"),
        )
        round_indices = (0, 0)

        result = truncate_oldest_rounds(
            responses=responses,
            round_indices=round_indices,
            budget=ContextBudget(max_tokens=10000),
            target_tokens=10000,
        )

        assert len(result) == 2
        assert result == responses

    def test_truncate_oldest_rounds_removes_oldest(self):
        """Should remove oldest round when exceeding budget."""
        # Create responses with predictable token counts
        r1 = Response(model_name="m1", answer="a" * 400)  # ~100 tokens
        r2 = Response(model_name="m2", answer="a" * 400)  # ~100 tokens
        r3 = Response(model_name="m3", answer="a" * 400)  # ~100 tokens (round 2)

        responses = (r1, r2, r3)
        round_indices = (0, 0, 1)  # First two from round 0, last from round 1

        # Target is 150 tokens, so should keep only round 1 (most recent)
        result = truncate_oldest_rounds(
            responses=responses,
            round_indices=round_indices,
            budget=ContextBudget(max_tokens=1000),
            target_tokens=150,
        )

        # Should keep only the most recent round (round 1)
        assert len(result) == 1
        assert result[0] == r3

    def test_truncate_oldest_rounds_keeps_most_recent_intact(self):
        """Most recent round should never be truncated."""
        responses = (
            Response(model_name="m1", answer="a" * 4000),  # ~1000 tokens
            Response(model_name="m2", answer="a" * 4000),  # ~1000 tokens (most recent)
        )
        round_indices = (0, 1)

        # Even with very low target, most recent round is kept
        result = truncate_oldest_rounds(
            responses=responses,
            round_indices=round_indices,
            budget=ContextBudget(max_tokens=2000),
            target_tokens=100,
        )

        # Should keep round 1 even though it exceeds target
        assert len(result) == 1
        assert result[0] == responses[1]

    def test_truncate_oldest_rounds_multiple_rounds(self):
        """Should progressively remove oldest rounds."""
        # Round 0: 2 responses
        r0_1 = Response(model_name="m1", answer="a" * 400)
        r0_2 = Response(model_name="m2", answer="a" * 400)
        # Round 1: 2 responses
        r1_1 = Response(model_name="m3", answer="a" * 400)
        r1_2 = Response(model_name="m4", answer="a" * 400)
        # Round 2: 1 response (most recent)
        r2_1 = Response(model_name="m5", answer="a" * 400)

        responses = (r0_1, r0_2, r1_1, r1_2, r2_1)
        round_indices = (0, 0, 1, 1, 2)

        # Target fits rounds 1 and 2 but not 0
        result = truncate_oldest_rounds(
            responses=responses,
            round_indices=round_indices,
            budget=ContextBudget(max_tokens=1000),
            target_tokens=350,
        )

        # Should drop round 0, keep rounds 1 and 2
        assert len(result) == 3
        assert r1_1 in result
        assert r1_2 in result
        assert r2_1 in result
        assert r0_1 not in result
        assert r0_2 not in result

    def test_truncate_oldest_rounds_mismatched_lengths(self):
        """Should raise error if responses and indices have different lengths."""
        responses = (Response(model_name="m1", answer="test"),)
        round_indices = (0, 1)  # Wrong length

        with pytest.raises(ValueError, match="must have same length"):
            truncate_oldest_rounds(
                responses=responses,
                round_indices=round_indices,
                budget=ContextBudget(max_tokens=1000),
                target_tokens=500,
            )

    def test_build_truncated_digest_empty(self):
        """Building digest from empty responses should work."""
        digest = build_truncated_digest(responses=(), max_tokens=1000)

        assert digest.common_points == ()
        assert digest.objections == ()
        assert digest.missing == ()
        assert digest.suggested_edits == ()

    def test_build_truncated_digest_with_approvals(self):
        """Digest should include approval summary."""
        responses = (
            Response(model_name="m1", answer="answer", approve=True),
            Response(model_name="m2", answer="answer", approve=True),
            Response(model_name="m3", answer="answer", approve=False),
        )

        digest = build_truncated_digest(responses=responses, max_tokens=1000)

        assert len(digest.common_points) > 0
        # Should note that 2/3 approved
        assert "2/3" in digest.common_points[0]

    def test_build_truncated_digest_with_critiques(self):
        """Digest should collect all critique fields."""
        responses = (
            Response(
                model_name="m1",
                answer="",
                approve=False,
                objections=("Obj 1", "Obj 2"),
                missing=("Missing 1",),
                edits=("Edit 1",),
            ),
            Response(
                model_name="m2",
                answer="",
                approve=False,
                objections=("Obj 3",),
                missing=("Missing 2",),
                edits=(),
            ),
        )

        digest = build_truncated_digest(responses=responses, max_tokens=1000)

        assert len(digest.objections) == 3
        assert "Obj 1" in digest.objections
        assert "Obj 2" in digest.objections
        assert "Obj 3" in digest.objections

        assert len(digest.missing) == 2
        assert "Missing 1" in digest.missing
        assert "Missing 2" in digest.missing

        assert len(digest.suggested_edits) == 1
        assert "Edit 1" in digest.suggested_edits


class TestContextIntegration:
    """Test integration of context budget with consensus runner."""

    def test_budget_tracking_across_rounds(self):
        """Test that budget tracking accumulates correctly across rounds."""
        budget = ContextBudget(max_tokens=1000)

        # Simulate round 0 usage
        round0_responses = [
            Response(model_name="m1", answer="a" * 200),  # ~50 tokens
            Response(model_name="m2", answer="a" * 200),  # ~50 tokens
        ]
        round0_tokens = sum(count_response_tokens(r) for r in round0_responses)
        budget = track_usage(budget, round0_tokens, round_idx=0)

        assert budget.used_tokens == round0_tokens

        # Simulate round 1 usage
        round1_responses = [
            Response(model_name="m1", answer="a" * 400),  # ~100 tokens
            Response(model_name="m2", answer="a" * 400),  # ~100 tokens
        ]
        round1_tokens = sum(count_response_tokens(r) for r in round1_responses)
        budget = track_usage(budget, round1_tokens, round_idx=1)

        assert budget.used_tokens == round0_tokens + round1_tokens
        assert len(budget.round_usage) == 2

    def test_budget_enforcement_triggers_truncation(self):
        """Test that exceeding budget triggers truncation."""
        budget = ContextBudget(max_tokens=1000, used_tokens=800)

        # Create responses that would exceed budget
        responses = (
            Response(model_name="m1", answer="a" * 400),  # Round 0
            Response(model_name="m2", answer="a" * 400),  # Round 0
            Response(model_name="m3", answer="a" * 400),  # Round 1
        )
        round_indices = (0, 0, 1)

        total_tokens = sum(count_response_tokens(r) for r in responses)

        # Check if would exceed
        assert would_exceed_budget(budget, total_tokens)

        # Apply truncation
        target_tokens = budget.max_tokens - budget.used_tokens
        truncated = truncate_oldest_rounds(
            responses=responses,
            round_indices=round_indices,
            budget=budget,
            target_tokens=target_tokens,
        )

        # Should have removed older rounds
        assert len(truncated) < len(responses)
        # Most recent round should be preserved
        assert responses[2] in truncated
