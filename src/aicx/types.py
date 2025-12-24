"""Shared dataclasses and type definitions for AI Consensus CLI."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Sequence


class ShareMode(str, Enum):
    """How to share information between participants."""

    DIGEST = "digest"
    RAW = "raw"


class Role(str, Enum):
    """Role of a model in the consensus process."""

    PARTICIPANT = "participant"
    MEDIATOR = "mediator"


class ExitCode(int, Enum):
    """CLI exit codes."""

    SUCCESS = 0
    CONFIG_ERROR = 1
    PROVIDER_ERROR = 2
    QUORUM_FAILURE = 3
    INTERNAL_ERROR = 4


@dataclass(frozen=True)
class RetryConfig:
    """Configuration for retry policy."""

    max_retries: int = 2
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True

    def __post_init__(self) -> None:
        if self.max_retries < 0:
            raise ValueError(f"max_retries must be >= 0, got {self.max_retries}")
        if self.base_delay_seconds <= 0:
            raise ValueError(f"base_delay_seconds must be > 0, got {self.base_delay_seconds}")
        if self.max_delay_seconds <= 0:
            raise ValueError(f"max_delay_seconds must be > 0, got {self.max_delay_seconds}")
        if self.exponential_base <= 0:
            raise ValueError(f"exponential_base must be > 0, got {self.exponential_base}")


@dataclass(frozen=True)
class ModelConfig:
    """Configuration for a single model."""

    name: str
    provider: str
    model_id: str
    temperature: float = 0.2
    max_tokens: int = 2048
    timeout_seconds: int = 60
    weight: float = 1.0
    retry: RetryConfig | None = None

    def __post_init__(self) -> None:
        if self.weight < 0:
            raise ValueError(f"weight must be >= 0, got {self.weight}")
        if self.temperature < 0 or self.temperature > 2:
            raise ValueError(f"temperature must be in [0, 2], got {self.temperature}")
        if self.max_tokens < 1:
            raise ValueError(f"max_tokens must be >= 1, got {self.max_tokens}")
        if self.timeout_seconds < 1:
            raise ValueError(f"timeout_seconds must be >= 1, got {self.timeout_seconds}")


@dataclass(frozen=True)
class RunConfig:
    """Configuration for a consensus run."""

    models: tuple[ModelConfig, ...]
    mediator: ModelConfig
    max_rounds: int = 3
    approval_ratio: float = 0.67
    change_threshold: float = 0.10
    max_context_tokens: int | None = None
    strict_json: bool = False
    verbose: bool = False
    share_mode: ShareMode = ShareMode.DIGEST

    def __post_init__(self) -> None:
        if len(self.models) < 2:
            raise ValueError(f"At least 2 models required, got {len(self.models)}")
        if self.max_rounds < 1:
            raise ValueError(f"max_rounds must be >= 1, got {self.max_rounds}")
        if not 0 <= self.approval_ratio <= 1:
            raise ValueError(f"approval_ratio must be in [0, 1], got {self.approval_ratio}")
        if not 0 <= self.change_threshold <= 1:
            raise ValueError(f"change_threshold must be in [0, 1], got {self.change_threshold}")
        if self.max_context_tokens is not None and self.max_context_tokens < 1:
            raise ValueError(f"max_context_tokens must be >= 1, got {self.max_context_tokens}")

    @property
    def quorum(self) -> int:
        """Calculate quorum as ceil(2/3 * participants)."""
        import math

        return math.ceil(len(self.models) * self.approval_ratio)


@dataclass(frozen=True)
class Digest:
    """Summary of participant responses for sharing."""

    common_points: tuple[str, ...] = field(default_factory=tuple)
    objections: tuple[str, ...] = field(default_factory=tuple)
    missing: tuple[str, ...] = field(default_factory=tuple)
    suggested_edits: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PromptRequest:
    """Request to send to a model."""

    user_prompt: str
    system_prompt: str
    round_index: int
    role: Role
    input_digest: Digest | None = None
    candidate_answer: str | None = None


@dataclass(frozen=True)
class Response:
    """Response from a model."""

    model_name: str
    answer: str
    approve: bool | None = None
    critical: bool | None = None
    objections: tuple[str, ...] = field(default_factory=tuple)
    missing: tuple[str, ...] = field(default_factory=tuple)
    edits: tuple[str, ...] = field(default_factory=tuple)
    confidence: float | None = None
    raw: str | None = None


@dataclass(frozen=True)
class MediatorState:
    """Current state of the mediator's synthesis."""

    candidate_answer: str
    rationale: str
    approval_count: int = 0
    critical_objections: tuple[str, ...] = field(default_factory=tuple)
    disagreement_summary: str | None = None


@dataclass(frozen=True)
class ConsensusResult:
    """Final result of a consensus run."""

    output: str
    exit_code: ExitCode
    consensus_reached: bool
    rounds_completed: int
    mediator_state: MediatorState | None = None
    responses: tuple[Response, ...] = field(default_factory=tuple)
    digest: Digest | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


# Error types


class AicxError(Exception):
    """Base exception for all aicx errors."""

    pass


class ConfigError(AicxError):
    """Configuration error (exit code 1)."""

    pass


class ProviderError(AicxError):
    """Provider/network error (exit code 2)."""

    def __init__(self, message: str, provider: str | None = None, code: str | None = None):
        super().__init__(message)
        self.provider = provider
        self.code = code


class ParseError(AicxError):
    """Malformed model output (treated as provider error)."""

    def __init__(self, message: str, raw_output: str | None = None):
        super().__init__(message)
        self.raw_output = raw_output


class QuorumError(AicxError):
    """Insufficient successful responses (exit code 3)."""

    def __init__(self, message: str, received: int, required: int):
        super().__init__(message)
        self.received = received
        self.required = required
