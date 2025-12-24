"""Shared dataclasses and type definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence


@dataclass(frozen=True)
class ModelConfig:
    name: str
    provider: str
    model_id: str
    temperature: float
    max_tokens: int
    timeout_seconds: int
    weight: float = 1.0


@dataclass(frozen=True)
class RunConfig:
    models: list[ModelConfig]
    mediator: ModelConfig
    max_rounds: int
    quorum: int
    approval_ratio: float
    change_threshold: float
    verbose: bool
    share_mode: str


@dataclass(frozen=True)
class PromptRequest:
    user_prompt: str
    system_prompt: str
    round_index: int
    role: str
    input_digest: "Digest | None" = None
    candidate_answer: str | None = None


@dataclass(frozen=True)
class Response:
    model_name: str
    answer: str
    approve: bool | None = None
    critical: bool | None = None
    objections: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    edits: list[str] = field(default_factory=list)
    confidence: float | None = None
    raw: str | None = None


@dataclass(frozen=True)
class Digest:
    common_points: list[str]
    objections: list[str]
    missing: list[str]
    suggested_edits: list[str]


@dataclass(frozen=True)
class MediatorState:
    candidate_answer: str
    rationale: str
    approval_count: int
    critical_objections: list[str]
    disagreement_summary: str | None = None


@dataclass(frozen=True)
class ConsensusResult:
    output: str
    exit_code: int
    mediator_state: MediatorState | None
    responses: Sequence[Response] = field(default_factory=list)
    digest: Digest | None = None
    rounds_completed: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
