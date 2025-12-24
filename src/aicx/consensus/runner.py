"""Consensus loop orchestration."""

from __future__ import annotations

from dataclasses import dataclass

from aicx.consensus.digest import build_digest, update_digest_from_critiques
from aicx.consensus.stop import should_stop
from aicx.logging import log_event
from aicx.types import (
    ConsensusResult,
    Digest,
    ExitCode,
    MediatorState,
    QuorumError,
    Response,
    RunConfig,
)


@dataclass(frozen=True)
class ConsensusContext:
    """Context for a consensus run."""

    prompt: str
    config: RunConfig


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

    # Phase 1: Collect independent answers (Round 1)
    # NOTE: This is a stub until provider adapters are implemented
    # In the real implementation, this would call participant models
    participant_responses = _collect_round1_responses(prompt, config)

    # Check quorum
    if len(participant_responses) < config.quorum:
        raise QuorumError(
            f"Insufficient responses: got {len(participant_responses)}, need {config.quorum}",
            received=len(participant_responses),
            required=config.quorum,
        )

    log_event("round_completed", payload={"round": 1, "responses": len(participant_responses)})

    # Phase 2: Mediator synthesizes candidate answer and builds digest
    # NOTE: This is a stub until mediator provider is implemented
    digest = build_digest(participant_responses)
    mediator_state = _synthesize_candidate(prompt, participant_responses, digest, config)

    log_event("synthesis_completed", payload={"candidate_length": len(mediator_state.candidate_answer)})

    all_responses = list(participant_responses)
    current_round = 1
    previous_candidate = None

    # Phase 3: Critique rounds (Round 2+)
    while current_round < config.max_rounds:
        current_round += 1

        # Collect critiques from participants
        # NOTE: This is a stub until provider adapters are implemented
        critiques = _collect_critique_responses(
            prompt,
            mediator_state.candidate_answer,
            digest,
            config,
        )

        log_event("round_completed", payload={"round": current_round, "critiques": len(critiques)})

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
                    critiques, critical_objections
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
        },
    )


def _collect_round1_responses(prompt: str, config: RunConfig) -> list[Response]:
    """
    Collect independent answers from all participants (Round 1).

    NOTE: This is a stub until provider adapters are implemented.
    In the real implementation, this would:
    1. Sort participants by name for determinism
    2. Call each participant model with the prompt
    3. Parse JSON responses into Response objects
    4. Handle failures and check quorum

    Args:
        prompt: User prompt
        config: Run configuration

    Returns:
        List of Response objects from participants
    """
    # Stub: Return empty list for now
    # Real implementation will call provider adapters
    log_event("round1_stub", payload={"participants": len(config.models)})

    # Sort models by name for deterministic ordering
    sorted_models = sorted(config.models, key=lambda m: m.name)

    # Placeholder responses
    responses = []
    for model in sorted_models:
        response = Response(
            model_name=model.name,
            answer=f"[Stub answer from {model.name}]",
        )
        responses.append(response)

    return responses


def _synthesize_candidate(
    prompt: str,
    responses: list[Response],
    digest: Digest,
    config: RunConfig,
) -> MediatorState:
    """
    Mediator synthesizes candidate answer from participant responses.

    NOTE: This is a stub until mediator provider is implemented.
    In the real implementation, this would:
    1. Call mediator model with all participant answers
    2. Parse JSON response into MediatorState
    3. Handle failures

    Args:
        prompt: User prompt
        responses: Participant responses
        digest: Digest of responses
        config: Run configuration

    Returns:
        MediatorState with candidate answer and rationale
    """
    # Stub: Return placeholder state
    log_event("synthesis_stub", payload={"responses": len(responses)})

    return MediatorState(
        candidate_answer="[Stub candidate answer from mediator]",
        rationale="Synthesized from participant responses",
        approval_count=0,
        critical_objections=(),
        disagreement_summary=None,
    )


def _collect_critique_responses(
    prompt: str,
    candidate_answer: str,
    digest: Digest,
    config: RunConfig,
) -> list[Response]:
    """
    Collect critique responses from participants (Round 2+).

    NOTE: This is a stub until provider adapters are implemented.
    In the real implementation, this would:
    1. Sort participants by name for determinism
    2. Call each participant model with candidate and digest
    3. Parse JSON responses into Response objects with critique fields
    4. Handle failures and check quorum

    Args:
        prompt: Original user prompt
        candidate_answer: Current candidate answer
        digest: Current digest
        config: Run configuration

    Returns:
        List of Response objects with critique data
    """
    # Stub: Return empty list for now
    log_event("critique_stub", payload={"participants": len(config.models)})

    # Sort models by name for deterministic ordering
    sorted_models = sorted(config.models, key=lambda m: m.name)

    # Placeholder critiques
    critiques = []
    for model in sorted_models:
        critique = Response(
            model_name=model.name,
            answer="",  # No new answer in critique
            approve=True,  # Stub: all approve
            critical=False,
            objections=(),
            missing=(),
            edits=(),
        )
        critiques.append(critique)

    return critiques


def _update_candidate(
    previous_candidate: str,
    critiques: list[Response],
    digest: Digest,
    config: RunConfig,
) -> MediatorState:
    """
    Mediator updates candidate based on critiques.

    NOTE: This is a stub until mediator provider is implemented.
    In the real implementation, this would:
    1. Call mediator model with critiques and digest
    2. Parse JSON response into updated MediatorState
    3. Handle failures

    Args:
        previous_candidate: Previous candidate answer
        critiques: Critique responses from participants
        digest: Current digest
        config: Run configuration

    Returns:
        Updated MediatorState
    """
    # Stub: Return same candidate for now
    log_event("update_stub", payload={"critiques": len(critiques)})

    return MediatorState(
        candidate_answer=previous_candidate,  # No changes in stub
        rationale="Updated based on critiques",
        approval_count=0,
        critical_objections=(),
        disagreement_summary=None,
    )


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


def _build_disagreement_summary(
    critiques: list[Response],
    critical_objections: tuple[str, ...],
) -> str:
    """
    Build a disagreement summary when consensus is not reached.

    Includes:
    - Top 3 unresolved objections
    - Any remaining missing items
    - A note explaining why consensus failed

    Args:
        critiques: List of critique responses
        critical_objections: Critical objections from critiques

    Returns:
        Formatted disagreement summary string
    """
    # Collect all objections and missing items
    all_objections = []
    all_missing = []

    for critique in critiques:
        if not critique.approve:
            all_objections.extend(critique.objections)
            all_missing.extend(critique.missing)

    # Build summary
    lines = ["Disagreement Summary:"]

    if critical_objections:
        lines.append(f"\nCritical objections ({len(critical_objections)}):")
        for obj in critical_objections[:3]:
            lines.append(f"- {obj}")

    if all_objections:
        lines.append(f"\nTop objections ({len(all_objections)}):")
        for obj in all_objections[:3]:
            lines.append(f"- {obj}")

    if all_missing:
        lines.append(f"\nMissing items ({len(all_missing)}):")
        for item in all_missing[:3]:
            lines.append(f"- {item}")

    lines.append("\nConsensus not reached within round limits.")

    return "\n".join(lines)
