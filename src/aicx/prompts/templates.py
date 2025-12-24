"""Prompt templates and rendering."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PromptTemplate:
    system: str
    user: str


def participant_prompt(user_prompt: str) -> PromptTemplate:
    system = (
        "You are a participant model in a consensus protocol. "
        "Return a strict JSON object with fields: "
        "answer (string), confidence (optional float 0-1)."
    )
    return PromptTemplate(system=system, user=user_prompt)


def critique_prompt(candidate_answer: str, digest: str) -> PromptTemplate:
    system = (
        "You are a participant model critiquing a candidate answer. "
        "Return strict JSON with fields: approve (bool), critical (bool), "
        "objections (list of strings), missing (list of strings), "
        "edits (list of strings), confidence (optional float 0-1)."
    )
    user = "Candidate answer:\n" + candidate_answer + "\n\nDigest:\n" + digest
    return PromptTemplate(system=system, user=user)


def mediator_synthesis_prompt(inputs: str) -> PromptTemplate:
    system = (
        "You are the mediator. Synthesize a candidate answer from participant responses. "
        "Return strict JSON with fields: candidate_answer, rationale, common_points, "
        "objections, missing, suggested_edits."
    )
    return PromptTemplate(system=system, user=inputs)


def mediator_update_prompt(candidate_answer: str, critiques: str) -> PromptTemplate:
    system = (
        "You are the mediator. Update the candidate answer using critiques. "
        "Return strict JSON with fields: candidate_answer, rationale."
    )
    user = "Candidate answer:\n" + candidate_answer + "\n\nCritiques:\n" + critiques
    return PromptTemplate(system=system, user=user)
