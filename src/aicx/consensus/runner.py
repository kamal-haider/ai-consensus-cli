"""Consensus loop orchestration."""

from __future__ import annotations

from dataclasses import dataclass

from aicx.logging import log_event
from aicx.types import ConsensusResult, Digest, MediatorState, Response, RunConfig


@dataclass(frozen=True)
class ConsensusContext:
    prompt: str
    config: RunConfig


def run_consensus(prompt: str, config: RunConfig, no_consensus_summary: bool = False) -> ConsensusResult:
    log_event("run_started", payload={"prompt": prompt})

    # Placeholder: return a deterministic stub until providers are implemented.
    mediator_state = MediatorState(
        candidate_answer="Consensus engine not implemented yet.",
        rationale="stub",
        approval_count=0,
        critical_objections=[],
        disagreement_summary=None,
    )

    output = mediator_state.candidate_answer
    if not no_consensus_summary and mediator_state.disagreement_summary:
        output += "\n\n" + mediator_state.disagreement_summary

    return ConsensusResult(
        output=output,
        exit_code=0,
        mediator_state=mediator_state,
        responses=[],
        digest=Digest(common_points=[], objections=[], missing=[], suggested_edits=[]),
        rounds_completed=0,
    )
