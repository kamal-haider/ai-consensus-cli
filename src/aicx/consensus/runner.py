"""Consensus loop orchestration."""

from __future__ import annotations

import json
from dataclasses import dataclass

from aicx.consensus.digest import build_digest, update_digest_from_critiques
from aicx.consensus.errors import check_round_responses
from aicx.consensus.stop import should_stop
from aicx.context.budget import ContextBudget, track_usage, would_exceed_budget
from aicx.context.tokens import count_response_tokens
from aicx.context.truncation import truncate_oldest_rounds
from aicx.logging import log_event
from aicx.models.factory import create_provider
from aicx.models.registry import ProviderAdapter
from aicx.prompts.templates import (
    critique_prompt,
    mediator_synthesis_prompt,
    mediator_update_prompt,
    participant_prompt,
)
from aicx.types import (
    ConsensusResult,
    Digest,
    ExitCode,
    MediatorState,
    ModelConfig,
    ParseError,
    PromptRequest,
    ProviderError,
    Response,
    Role,
    RunConfig,
)


@dataclass(frozen=True)
class ConsensusContext:
    """Context for a consensus run."""

    prompt: str
    config: RunConfig


def _format_digest(digest: Digest) -> str:
    """Format a digest as a string for prompts.

    Args:
        digest: Digest to format.

    Returns:
        Formatted string representation.
    """
    lines = []

    if digest.common_points:
        lines.append("Common points:")
        for point in digest.common_points:
            lines.append(f"  - {point}")

    if digest.objections:
        lines.append("Objections:")
        for obj in digest.objections:
            lines.append(f"  - {obj}")

    if digest.missing:
        lines.append("Missing:")
        for item in digest.missing:
            lines.append(f"  - {item}")

    if digest.suggested_edits:
        lines.append("Suggested edits:")
        for edit in digest.suggested_edits:
            lines.append(f"  - {edit}")

    return "\n".join(lines) if lines else "(No digest available)"


def _format_responses_for_mediator(responses: list[Response]) -> str:
    """Format participant responses for mediator synthesis.

    Args:
        responses: List of participant responses.

    Returns:
        Formatted string with all answers.
    """
    lines = []
    for i, response in enumerate(responses, 1):
        lines.append(f"Participant {i} ({response.model_name}):")
        lines.append(response.answer)
        lines.append("")
    return "\n".join(lines)


def _format_critiques_for_mediator(critiques: list[Response]) -> str:
    """Format critique responses for mediator update.

    Args:
        critiques: List of critique responses.

    Returns:
        Formatted string with all critiques.
    """
    lines = []
    for critique in critiques:
        lines.append(f"Critique from {critique.model_name}:")
        lines.append(f"  Approve: {critique.approve}")
        lines.append(f"  Critical: {critique.critical}")
        if critique.objections:
            lines.append(f"  Objections: {', '.join(critique.objections)}")
        if critique.missing:
            lines.append(f"  Missing: {', '.join(critique.missing)}")
        if critique.edits:
            lines.append(f"  Suggested edits: {', '.join(critique.edits)}")
        lines.append("")
    return "\n".join(lines)


def _create_providers_for_config(config: RunConfig) -> dict[str, ProviderAdapter]:
    """Create providers for all models in config.

    Args:
        config: Run configuration.

    Returns:
        Dictionary mapping model names to providers.
    """
    providers = {}
    for model in config.models:
        providers[model.name] = create_provider(model)
    return providers


def run_consensus(
    prompt: str,
    config: RunConfig,
    no_consensus_summary: bool = False,
) -> ConsensusResult:
    """
    Run the consensus loop.

    This is the main orchestrator that coordinates:
    1. Round 1: Independent participant answers
    2. Mediator synthesis and digest construction
    3. Round 2+: Critique rounds with mediator updates
    4. Stop condition checking

    Args:
        prompt: User prompt to answer
        config: Run configuration
        no_consensus_summary: If True, omit disagreement summary from output

    Returns:
        ConsensusResult with final answer and metadata
    """
    log_event("run_started", payload={"prompt": prompt})

    # Initialize context budget if configured
    budget: ContextBudget | None = None
    if config.max_context_tokens is not None:
        budget = ContextBudget(max_tokens=config.max_context_tokens)
        log_event("budget_initialized", payload={"max_tokens": config.max_context_tokens})

    # Create providers once for reuse
    providers = _create_providers_for_config(config)
    mediator_provider = create_provider(config.mediator)

    # Phase 1: Collect independent answers (Round 1)
    participant_responses, failed_models_r1 = _collect_round1_responses(
        prompt, config, providers
    )

    # Check quorum (raises ZeroResponseError or QuorumError if not met)
    check_round_responses(participant_responses, config, round_index=1)

    log_event("round_completed", payload={"round": 1, "responses": len(participant_responses)})

    # Track token usage for round 1
    if budget is not None:
        round_tokens = sum(count_response_tokens(r) for r in participant_responses)
        budget = track_usage(budget, round_tokens, round_idx=0)
        log_event("budget_tracked", payload={
            "round": 1,
            "round_tokens": round_tokens,
            "total_used": budget.used_tokens,
        })

    # Phase 2: Mediator synthesizes candidate answer and builds digest
    digest = build_digest(participant_responses)
    mediator_state = _synthesize_candidate(
        prompt, participant_responses, digest, config, mediator_provider
    )

    log_event("synthesis_completed", payload={"candidate_length": len(mediator_state.candidate_answer)})

    all_responses = list(participant_responses)
    all_failed_models = list(failed_models_r1)
    round_indices = [0] * len(participant_responses)  # Track which round each response is from
    current_round = 1
    previous_candidate = None

    # Phase 3: Critique rounds (Round 2+)
    while current_round < config.max_rounds:
        current_round += 1

        # Apply context budget truncation if needed before calling mediator
        responses_for_mediator = all_responses
        if budget is not None:
            # Estimate tokens needed for this round
            estimated_new_tokens = sum(count_response_tokens(r) for r in all_responses)

            if would_exceed_budget(budget, estimated_new_tokens):
                # Need to truncate oldest rounds
                target_tokens = budget.max_tokens - budget.used_tokens
                responses_for_mediator = list(truncate_oldest_rounds(
                    tuple(all_responses),
                    tuple(round_indices),
                    budget,
                    target_tokens,
                ))

                dropped_count = len(all_responses) - len(responses_for_mediator)
                if dropped_count > 0:
                    log_event("context_truncated", payload={
                        "round": current_round,
                        "dropped_responses": dropped_count,
                        "target_tokens": target_tokens,
                    })

        # Collect critiques from participants
        critiques, failed_models_critique = _collect_critique_responses(
            prompt,
            mediator_state.candidate_answer,
            digest,
            config,
            current_round,
            providers,
        )

        # Check quorum for critique round
        check_round_responses(critiques, config, round_index=current_round)

        # Track failed models across all rounds
        all_failed_models.extend(failed_models_critique)

        log_event("round_completed", payload={"round": current_round, "critiques": len(critiques)})

        # Track token usage for this round
        if budget is not None:
            round_tokens = sum(count_response_tokens(r) for r in critiques)
            budget = track_usage(budget, round_tokens, round_idx=current_round - 1)
            log_event("budget_tracked", payload={
                "round": current_round,
                "round_tokens": round_tokens,
                "total_used": budget.used_tokens,
            })

        # Count approvals and critical objections
        approval_count, critical_objections = _analyze_critiques(critiques)

        # Update digest based on critiques
        digest = update_digest_from_critiques(digest, critiques)

        # Check stop conditions
        stop, reason = should_stop(
            current_round=current_round,
            approval_count=approval_count,
            critical_objections=critical_objections,
            previous_candidate=previous_candidate,
            new_candidate=mediator_state.candidate_answer,
            critiques=critiques,
            config=config,
        )

        if stop:
            log_event("stop_condition_met", payload={"reason": reason, "round": current_round})

            # Update mediator state with final approval count and critical objections
            mediator_state = MediatorState(
                candidate_answer=mediator_state.candidate_answer,
                rationale=mediator_state.rationale,
                approval_count=approval_count,
                critical_objections=critical_objections,
                disagreement_summary=_build_disagreement_summary(
                    critiques,
                    critical_objections,
                    approval_count,
                    len(config.models),
                    config.approval_ratio,
                ) if reason != "consensus_reached" else None,
            )
            break

        # Update candidate based on critiques
        previous_candidate = mediator_state.candidate_answer
        mediator_state = _update_candidate(
            previous_candidate,
            critiques,
            digest,
            config,
            mediator_provider,
        )

        # Update mediator state with current approval metrics
        mediator_state = MediatorState(
            candidate_answer=mediator_state.candidate_answer,
            rationale=mediator_state.rationale,
            approval_count=approval_count,
            critical_objections=critical_objections,
            disagreement_summary=None,  # Will be set if we hit max rounds
        )

        all_responses.extend(critiques)
        round_indices.extend([current_round - 1] * len(critiques))  # Add round indices for critiques

        log_event("candidate_updated", payload={"round": current_round})

    # Determine consensus status
    consensus_reached = (
        mediator_state.approval_count >= config.quorum
        and len(mediator_state.critical_objections) == 0
    )

    # Build final output
    output = mediator_state.candidate_answer
    if not no_consensus_summary and mediator_state.disagreement_summary:
        output += "\n\n" + mediator_state.disagreement_summary

    exit_code = ExitCode.SUCCESS if consensus_reached else ExitCode.SUCCESS

    return ConsensusResult(
        output=output,
        exit_code=exit_code,
        consensus_reached=consensus_reached,
        rounds_completed=current_round,
        mediator_state=mediator_state,
        responses=tuple(all_responses),
        digest=digest,
        metadata={
            "prompt": prompt,
            "participants": len(config.models),
            "quorum": config.quorum,
            "failed_models": tuple(sorted(set(all_failed_models))),
        },
    )


def _collect_round1_responses(
    prompt: str,
    config: RunConfig,
    providers: dict[str, ProviderAdapter] | None = None,
) -> tuple[list[Response], tuple[str, ...]]:
    """
    Collect independent answers from all participants (Round 1).

    Args:
        prompt: User prompt
        config: Run configuration
        providers: Optional pre-created providers (uses factory if not provided)

    Returns:
        Tuple of (successful_responses, failed_model_names)
    """
    log_event("round1_started", payload={"participants": len(config.models)})

    # Create providers if not provided
    if providers is None:
        providers = _create_providers_for_config(config)

    # Sort models by name for deterministic ordering
    sorted_models = sorted(config.models, key=lambda m: m.name)

    responses = []
    failed_models = []

    for model in sorted_models:
        provider = providers.get(model.name)
        if provider is None:
            log_event("provider_missing", payload={"model": model.name})
            failed_models.append(model.name)
            continue

        # Build the prompt
        template = participant_prompt(prompt)
        request = PromptRequest(
            user_prompt=template.user,
            system_prompt=template.system,
            round_index=0,
            role=Role.PARTICIPANT,
        )

        try:
            response = provider.create_chat_completion(request)
            responses.append(response)
            log_event("response_received", payload={
                "model": model.name,
                "answer_length": len(response.answer),
            })
        except (ProviderError, ParseError) as e:
            log_event("response_failed", payload={
                "model": model.name,
                "error": str(e),
            })
            failed_models.append(model.name)

    return responses, tuple(failed_models)


def _synthesize_candidate(
    prompt: str,
    responses: list[Response],
    digest: Digest,
    config: RunConfig,
    mediator_provider: ProviderAdapter | None = None,
) -> MediatorState:
    """
    Mediator synthesizes candidate answer from participant responses.

    Args:
        prompt: User prompt
        responses: Participant responses
        digest: Digest of responses
        config: Run configuration
        mediator_provider: Optional pre-created mediator provider

    Returns:
        MediatorState with candidate answer and rationale
    """
    log_event("synthesis_started", payload={"responses": len(responses)})

    # Create mediator provider if not provided
    if mediator_provider is None:
        mediator_provider = create_provider(config.mediator)

    # Format responses for the mediator
    inputs = _format_responses_for_mediator(responses)

    # Build the prompt
    template = mediator_synthesis_prompt(inputs)
    request = PromptRequest(
        user_prompt=template.user,
        system_prompt=template.system,
        round_index=0,
        role=Role.MEDIATOR,
    )

    try:
        response = mediator_provider.create_chat_completion(request)

        # Parse the mediator response - it should contain candidate_answer and rationale
        # The response.answer contains the raw JSON, we need to parse it
        raw = response.raw or response.answer
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            # Fallback: use the answer field directly
            parsed = {"candidate_answer": response.answer, "rationale": ""}

        candidate_answer = parsed.get("candidate_answer", response.answer)
        rationale = parsed.get("rationale", "")

        log_event("synthesis_completed", payload={
            "candidate_length": len(candidate_answer),
        })

        return MediatorState(
            candidate_answer=candidate_answer,
            rationale=rationale,
            approval_count=0,
            critical_objections=(),
            disagreement_summary=None,
        )

    except (ProviderError, ParseError) as e:
        # Mediator failure is critical - re-raise
        log_event("synthesis_failed", payload={"error": str(e)})
        raise


def _collect_critique_responses(
    prompt: str,
    candidate_answer: str,
    digest: Digest,
    config: RunConfig,
    round_index: int,
    providers: dict[str, ProviderAdapter] | None = None,
) -> tuple[list[Response], tuple[str, ...]]:
    """
    Collect critique responses from participants (Round 2+).

    Args:
        prompt: Original user prompt
        candidate_answer: Current candidate answer
        digest: Current digest
        config: Run configuration
        round_index: Current round number
        providers: Optional pre-created providers

    Returns:
        Tuple of (successful_critiques, failed_model_names)
    """
    log_event("critique_started", payload={
        "round": round_index,
        "participants": len(config.models),
    })

    # Create providers if not provided
    if providers is None:
        providers = _create_providers_for_config(config)

    # Sort models by name for deterministic ordering
    sorted_models = sorted(config.models, key=lambda m: m.name)

    critiques = []
    failed_models = []

    # Format the digest
    digest_str = _format_digest(digest)

    for model in sorted_models:
        provider = providers.get(model.name)
        if provider is None:
            log_event("provider_missing", payload={"model": model.name})
            failed_models.append(model.name)
            continue

        # Build the critique prompt
        template = critique_prompt(candidate_answer, digest_str)
        request = PromptRequest(
            user_prompt=template.user,
            system_prompt=template.system,
            round_index=round_index,
            role=Role.PARTICIPANT,
            candidate_answer=candidate_answer,
            input_digest=digest,
        )

        try:
            response = provider.create_chat_completion(request)
            critiques.append(response)
            log_event("critique_received", payload={
                "model": model.name,
                "approve": response.approve,
                "critical": response.critical,
            })
        except (ProviderError, ParseError) as e:
            log_event("critique_failed", payload={
                "model": model.name,
                "error": str(e),
            })
            failed_models.append(model.name)

    return critiques, tuple(failed_models)


def _update_candidate(
    previous_candidate: str,
    critiques: list[Response],
    digest: Digest,
    config: RunConfig,
    mediator_provider: ProviderAdapter | None = None,
) -> MediatorState:
    """
    Mediator updates candidate based on critiques.

    Args:
        previous_candidate: Previous candidate answer
        critiques: Critique responses from participants
        digest: Current digest
        config: Run configuration
        mediator_provider: Optional pre-created mediator provider

    Returns:
        Updated MediatorState
    """
    log_event("update_started", payload={"critiques": len(critiques)})

    # Create mediator provider if not provided
    if mediator_provider is None:
        mediator_provider = create_provider(config.mediator)

    # Format critiques for the mediator
    critiques_str = _format_critiques_for_mediator(critiques)

    # Build the prompt
    template = mediator_update_prompt(previous_candidate, critiques_str)
    request = PromptRequest(
        user_prompt=template.user,
        system_prompt=template.system,
        round_index=1,  # Update is always after round 1
        role=Role.MEDIATOR,
        candidate_answer=previous_candidate,
    )

    try:
        response = mediator_provider.create_chat_completion(request)

        # Parse the mediator response
        raw = response.raw or response.answer
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            # Fallback: use the answer field directly
            parsed = {"candidate_answer": response.answer, "rationale": ""}

        candidate_answer = parsed.get("candidate_answer", response.answer)
        rationale = parsed.get("rationale", "")

        log_event("update_completed", payload={
            "candidate_length": len(candidate_answer),
        })

        return MediatorState(
            candidate_answer=candidate_answer,
            rationale=rationale,
            approval_count=0,
            critical_objections=(),
            disagreement_summary=None,
        )

    except (ProviderError, ParseError) as e:
        # Mediator failure is critical - re-raise
        log_event("update_failed", payload={"error": str(e)})
        raise


def _analyze_critiques(critiques: list[Response]) -> tuple[int, tuple[str, ...]]:
    """
    Analyze critiques to count approvals and extract critical objections.

    Args:
        critiques: List of critique responses

    Returns:
        Tuple of (approval_count, critical_objections)
    """
    approval_count = 0
    critical_objections = []

    for critique in critiques:
        if critique.approve:
            approval_count += 1

        if critique.critical and critique.objections:
            critical_objections.extend(critique.objections)

    return approval_count, tuple(critical_objections)


def _calculate_confidence(
    approval_count: int,
    total_participants: int,
    critical_count: int,
    approval_ratio: float,
) -> str:
    """
    Calculate a confidence indicator based on consensus metrics.

    Args:
        approval_count: Number of approvals received
        total_participants: Total number of participants
        critical_count: Number of critical objections
        approval_ratio: Required approval ratio

    Returns:
        Confidence level: "HIGH", "MEDIUM", or "LOW"
    """
    if total_participants == 0:
        return "LOW"

    actual_ratio = approval_count / total_participants

    # HIGH: >= required ratio and no critical objections
    if actual_ratio >= approval_ratio and critical_count == 0:
        return "HIGH"

    # MEDIUM: >= 50% approval and <= 1 critical objection
    if actual_ratio >= 0.5 and critical_count <= 1:
        return "MEDIUM"

    # LOW: otherwise
    return "LOW"


def _build_disagreement_summary(
    critiques: list[Response],
    critical_objections: tuple[str, ...],
    approval_count: int,
    total_participants: int,
    approval_ratio: float,
) -> str:
    """
    Build a disagreement summary when consensus is not reached.

    Includes:
    - Consensus status with approval count
    - Confidence indicator
    - Top unresolved issues

    Args:
        critiques: List of critique responses
        critical_objections: Critical objections from critiques
        approval_count: Number of approvals
        total_participants: Total number of participants
        approval_ratio: Required approval ratio

    Returns:
        Formatted disagreement summary string
    """
    # Calculate confidence
    confidence = _calculate_confidence(
        approval_count, total_participants, len(critical_objections), approval_ratio
    )

    # Collect all objections and missing items from non-approving critiques
    all_objections = []
    all_missing = []

    for critique in critiques:
        if not critique.approve:
            all_objections.extend(critique.objections)
            all_missing.extend(critique.missing)

    # Build summary with clear structure
    lines = ["---"]
    lines.append(
        f"Consensus: NOT REACHED ({approval_count}/{total_participants} approvals, "
        f"{len(critical_objections)} critical objection{'s' if len(critical_objections) != 1 else ''})"
    )
    lines.append(f"Confidence: {confidence}")

    # Add unresolved issues if any
    has_issues = critical_objections or all_objections or all_missing
    if has_issues:
        lines.append("")
        lines.append("Unresolved Issues:")

        # Critical objections first
        for obj in critical_objections[:2]:
            lines.append(f"- Critical: {obj}")

        # Then regular objections
        remaining_slots = 3 - min(len(critical_objections), 2)
        for obj in all_objections[:remaining_slots]:
            lines.append(f"- Objection: {obj}")

        # Then missing items
        for item in all_missing[:2]:
            lines.append(f"- Missing: {item}")

    return "\n".join(lines)
