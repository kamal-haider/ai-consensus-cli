"""Prompt templates and rendering."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PromptTemplate:
    system: str
    user: str


def participant_prompt(user_prompt: str) -> PromptTemplate:
    """Generate Round 1 participant prompt.

    Args:
        user_prompt: The user's question or prompt to answer.

    Returns:
        PromptTemplate with system instructions and user prompt.
    """
    system = (
        "You are a participant model in a consensus protocol. "
        "Your role is to provide the best possible answer to the user prompt.\n\n"
        "You must respond with a strict JSON object containing:\n"
        "- answer: string (required) - Your complete answer to the prompt\n"
        "- confidence: float (optional) - Your confidence level from 0 to 1\n\n"
        "Do not include any text outside the JSON object."
    )
    return PromptTemplate(system=system, user=user_prompt)


def critique_prompt(candidate_answer: str, digest: str) -> PromptTemplate:
    """Generate Round 2+ participant critique prompt.

    Args:
        candidate_answer: The current candidate answer to critique.
        digest: Summary of participant feedback.

    Returns:
        PromptTemplate with critique instructions and context.
    """
    system = (
        "You are a participant model critiquing a candidate answer. "
        "Your role is to evaluate the candidate answer and provide constructive feedback.\n\n"
        "You must respond with a strict JSON object containing:\n"
        "- approve: bool (required) - Whether you approve this answer\n"
        "- critical: bool (required) - Whether you have critical objections\n"
        "- objections: list of strings (required) - Specific objections or concerns\n"
        "- missing: list of strings (required) - Important missing information\n"
        "- edits: list of strings (required) - Suggested improvements or edits\n"
        "- confidence: float (optional) - Your confidence level from 0 to 1\n\n"
        "Critical criteria:\n"
        "- Mark critical=true ONLY for factual errors or advice that could cause harm\n"
        "- Do NOT mark critical for style issues or minor omissions\n\n"
        "Do not include any text outside the JSON object."
    )
    user = f"Candidate answer:\n{candidate_answer}\n\nDigest:\n{digest}"
    return PromptTemplate(system=system, user=user)


def mediator_synthesis_prompt(inputs: str) -> PromptTemplate:
    """Generate mediator synthesis prompt for Round 1.

    Args:
        inputs: Formatted participant responses to synthesize.

    Returns:
        PromptTemplate with synthesis instructions and participant inputs.
    """
    system = (
        "You are the mediator in a consensus protocol. "
        "Your role is to synthesize a candidate answer based on all participant responses.\n\n"
        "You must respond with a strict JSON object containing:\n"
        "- candidate_answer: string (required) - The synthesized answer\n"
        "- rationale: string (required) - Explanation of your synthesis approach\n"
        "- common_points: list of strings (required) - Points of agreement among participants\n"
        "- objections: list of strings (required) - Conflicting viewpoints or concerns\n"
        "- missing: list of strings (required) - Information gaps identified\n"
        "- suggested_edits: list of strings (required) - Potential improvements\n\n"
        "Do not include any text outside the JSON object."
    )
    return PromptTemplate(system=system, user=inputs)


def mediator_update_prompt(candidate_answer: str, critiques: str) -> PromptTemplate:
    """Generate mediator update prompt for Round 2+.

    Args:
        candidate_answer: The current candidate answer to update.
        critiques: Formatted critique responses from participants.

    Returns:
        PromptTemplate with update instructions and critique context.
    """
    system = (
        "You are the mediator in a consensus protocol. "
        "Your role is to update the candidate answer based on participant critiques.\n\n"
        "You must respond with a strict JSON object containing:\n"
        "- candidate_answer: string (required) - The updated answer incorporating feedback\n"
        "- rationale: string (required) - Explanation of how you addressed critiques\n\n"
        "Do not include any text outside the JSON object."
    )
    user = f"Candidate answer:\n{candidate_answer}\n\nCritiques:\n{critiques}"
    return PromptTemplate(system=system, user=user)
