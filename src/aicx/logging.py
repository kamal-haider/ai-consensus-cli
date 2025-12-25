"""Verbose audit logging with event types and redaction."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from typing import Any


_is_verbose = False

# Patterns for redacting sensitive information in strings
_SECRET_PATTERNS = [
    re.compile(r'(api[_-]?key\s*[=:]\s*)["\']?([a-zA-Z0-9_-]+)["\']?', re.IGNORECASE),
    re.compile(r'(OPENAI_API_KEY\s*[=:]\s*)["\']?([a-zA-Z0-9_-]+)["\']?', re.IGNORECASE),
    re.compile(r'(ANTHROPIC_API_KEY\s*[=:]\s*)["\']?([a-zA-Z0-9_-]+)["\']?', re.IGNORECASE),
    re.compile(r'(GEMINI_API_KEY\s*[=:]\s*)["\']?([a-zA-Z0-9_-]+)["\']?', re.IGNORECASE),
    re.compile(r'(bearer\s+)[a-zA-Z0-9_-]+', re.IGNORECASE),
    re.compile(r'(token\s*[=:]\s*)["\']?([a-zA-Z0-9_.-]+)["\']?', re.IGNORECASE),
]

# Keys that should have their values redacted in dicts
# Use word boundaries to avoid matching e.g. "original_tokens"
_SENSITIVE_KEYS = re.compile(r'^(api[_-]?key|token|secret|password|credential)$', re.IGNORECASE)


def configure_logging(verbose: bool) -> None:
    """Enable or disable verbose logging.

    Args:
        verbose: If True, log events to stderr as JSONL.
    """
    global _is_verbose
    _is_verbose = verbose


def _redact_secrets(obj: Any) -> Any:
    """Recursively redact secrets from a data structure.

    Args:
        obj: Any JSON-serializable object.

    Returns:
        A copy of the object with secrets replaced by [REDACTED].
    """
    if isinstance(obj, str):
        for pattern in _SECRET_PATTERNS:
            obj = pattern.sub(r'\1[REDACTED]', obj)
        return obj
    elif isinstance(obj, dict):
        result = {}
        for k, v in obj.items():
            # If the key matches a sensitive pattern, redact the value
            if isinstance(k, str) and _SENSITIVE_KEYS.search(k):
                result[k] = "[REDACTED]"
            else:
                result[k] = _redact_secrets(v)
        return result
    elif isinstance(obj, (list, tuple)):
        return type(obj)(_redact_secrets(item) for item in obj)
    else:
        return obj


def log_event(
    event: str,
    *,
    payload: dict[str, Any] | None = None,
    round_index: int | None = None,
    model: str | None = None,
) -> None:
    """Log an event to stderr if verbose mode is enabled.

    Args:
        event: Event type (e.g., 'config_loaded', 'model_request').
        payload: Optional event-specific data.
        round_index: Optional round number (0-indexed).
        model: Optional model name.
    """
    if not _is_verbose:
        return

    # Build record with stable key ordering
    record = {
        "event": event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if round_index is not None:
        record["round"] = round_index

    if model is not None:
        record["model"] = model

    # Redact secrets from payload
    if payload is not None:
        record["payload"] = _redact_secrets(payload)
    else:
        record["payload"] = {}

    # Write to stderr with sorted keys for determinism
    sys.stderr.write(json.dumps(record, sort_keys=True) + "\n")


def log_config_loaded(config: dict[str, Any]) -> None:
    """Log configuration loaded event.

    Args:
        config: Configuration dictionary (will be redacted).
    """
    log_event("config_loaded", payload={"config": config})


def log_round_started(round_index: int, num_participants: int) -> None:
    """Log round started event.

    Args:
        round_index: Round number (0-indexed).
        num_participants: Number of participating models.
    """
    log_event(
        "round_started",
        round_index=round_index,
        payload={"num_participants": num_participants},
    )


def log_model_request(
    model: str,
    round_index: int,
    prompt_length: int,
    has_candidate: bool,
) -> None:
    """Log model request event.

    Args:
        model: Model name.
        round_index: Round number (0-indexed).
        prompt_length: Length of the prompt in characters.
        has_candidate: Whether a candidate answer was included.
    """
    log_event(
        "model_request",
        model=model,
        round_index=round_index,
        payload={
            "prompt_length": prompt_length,
            "has_candidate": has_candidate,
        },
    )


def log_model_response(
    model: str,
    round_index: int,
    response_length: int,
    approve: bool | None = None,
    critical: bool | None = None,
) -> None:
    """Log model response event.

    Args:
        model: Model name.
        round_index: Round number (0-indexed).
        response_length: Length of the response in characters.
        approve: Whether the model approved (round 2+).
        critical: Whether the model raised critical objections (round 2+).
    """
    payload: dict[str, Any] = {"response_length": response_length}

    if approve is not None:
        payload["approve"] = approve

    if critical is not None:
        payload["critical"] = critical

    log_event(
        "model_response",
        model=model,
        round_index=round_index,
        payload=payload,
    )


def log_parse_recovery_attempt(
    model: str,
    round_index: int,
    error: str,
    strategy: str,
) -> None:
    """Log parse recovery attempt event.

    Args:
        model: Model name.
        round_index: Round number (0-indexed).
        error: Error message from parsing.
        strategy: Recovery strategy being attempted.
    """
    log_event(
        "parse_recovery_attempt",
        model=model,
        round_index=round_index,
        payload={
            "error": error,
            "strategy": strategy,
        },
    )


def log_context_truncated(
    model: str,
    round_index: int,
    original_tokens: int,
    truncated_tokens: int,
) -> None:
    """Log context truncation event.

    Args:
        model: Model name.
        round_index: Round number (0-indexed).
        original_tokens: Original token count.
        truncated_tokens: Token count after truncation.
    """
    log_event(
        "context_truncated",
        model=model,
        round_index=round_index,
        payload={
            "original_tokens": original_tokens,
            "truncated_tokens": truncated_tokens,
        },
    )


def log_mediator_update(
    round_index: int,
    candidate_length: int,
    approval_count: int,
    critical_count: int,
) -> None:
    """Log mediator update event.

    Args:
        round_index: Round number (0-indexed).
        candidate_length: Length of candidate answer in characters.
        approval_count: Number of approvals.
        critical_count: Number of critical objections.
    """
    log_event(
        "mediator_update",
        round_index=round_index,
        payload={
            "candidate_length": candidate_length,
            "approval_count": approval_count,
            "critical_count": critical_count,
        },
    )


def log_consensus_check(
    round_index: int,
    consensus_reached: bool,
    approval_ratio: float,
    required_ratio: float,
    critical_count: int,
) -> None:
    """Log consensus check event.

    Args:
        round_index: Round number (0-indexed).
        consensus_reached: Whether consensus was reached.
        approval_ratio: Actual approval ratio.
        required_ratio: Required approval ratio.
        critical_count: Number of critical objections.
    """
    log_event(
        "consensus_check",
        round_index=round_index,
        payload={
            "consensus_reached": consensus_reached,
            "approval_ratio": approval_ratio,
            "required_ratio": required_ratio,
            "critical_count": critical_count,
        },
    )


def log_run_complete(
    rounds_completed: int,
    consensus_reached: bool,
    exit_code: int,
) -> None:
    """Log run complete event.

    Args:
        rounds_completed: Number of rounds completed.
        consensus_reached: Whether consensus was reached.
        exit_code: Exit code.
    """
    log_event(
        "run_complete",
        payload={
            "rounds_completed": rounds_completed,
            "consensus_reached": consensus_reached,
            "exit_code": exit_code,
        },
    )


def log_error(
    error_type: str,
    message: str,
    round_index: int | None = None,
    model: str | None = None,
) -> None:
    """Log error event.

    Args:
        error_type: Type of error (e.g., 'ConfigError', 'ProviderError').
        message: Error message (will be redacted).
        round_index: Optional round number.
        model: Optional model name.
    """
    log_event(
        "error",
        round_index=round_index,
        model=model,
        payload={
            "error_type": error_type,
            "message": message,
        },
    )
