"""JSON parsing with recovery for model responses."""

from __future__ import annotations

import json
import re
from typing import Any

from aicx.types import ParseError, Response


def parse_participant_response(
    raw: str, model_name: str, strict_json: bool = False
) -> Response:
    """Parse participant Round 1 response.

    Args:
        raw: Raw text response from the model.
        model_name: Name of the model that generated the response.
        strict_json: If True, skip recovery and fail on first parse error.

    Returns:
        Response object with parsed fields.

    Raises:
        ParseError: If JSON parsing fails (after recovery attempts if not strict).
    """
    parsed = _parse_json(raw, strict_json)

    # Extract required fields
    answer = parsed.get("answer")
    if not isinstance(answer, str):
        raise ParseError(
            f"Missing or invalid 'answer' field in participant response",
            raw_output=raw,
        )

    # Extract optional fields with defaults
    confidence = parsed.get("confidence")
    if confidence is not None and not isinstance(confidence, (int, float)):
        confidence = None

    return Response(
        model_name=model_name,
        answer=answer,
        confidence=float(confidence) if confidence is not None else None,
        raw=raw,
    )


def parse_critique_response(
    raw: str, model_name: str, strict_json: bool = False
) -> Response:
    """Parse participant Round 2+ critique response.

    Args:
        raw: Raw text response from the model.
        model_name: Name of the model that generated the response.
        strict_json: If True, skip recovery and fail on first parse error.

    Returns:
        Response object with parsed critique fields.

    Raises:
        ParseError: If JSON parsing fails or required fields are missing.
    """
    parsed = _parse_json(raw, strict_json)

    # Extract required fields
    approve = parsed.get("approve")
    if not isinstance(approve, bool):
        raise ParseError(
            f"Missing or invalid 'approve' field in critique response",
            raw_output=raw,
        )

    critical = parsed.get("critical")
    if not isinstance(critical, bool):
        raise ParseError(
            f"Missing or invalid 'critical' field in critique response",
            raw_output=raw,
        )

    # Extract list fields with defaults
    objections = _parse_string_list(parsed.get("objections", []))
    missing = _parse_string_list(parsed.get("missing", []))
    edits = _parse_string_list(parsed.get("edits", []))

    # Extract optional confidence
    confidence = parsed.get("confidence")
    if confidence is not None and not isinstance(confidence, (int, float)):
        confidence = None

    return Response(
        model_name=model_name,
        answer="",  # Critiques don't have an answer field
        approve=approve,
        critical=critical,
        objections=tuple(objections),
        missing=tuple(missing),
        edits=tuple(edits),
        confidence=float(confidence) if confidence is not None else None,
        raw=raw,
    )


def parse_mediator_synthesis(raw: str, strict_json: bool = False) -> dict[str, Any]:
    """Parse mediator synthesis response.

    Args:
        raw: Raw text response from the mediator.
        strict_json: If True, skip recovery and fail on first parse error.

    Returns:
        Dictionary with synthesis fields: candidate_answer, rationale, etc.

    Raises:
        ParseError: If JSON parsing fails or required fields are missing.
    """
    parsed = _parse_json(raw, strict_json)

    # Validate required fields
    candidate_answer = parsed.get("candidate_answer")
    if not isinstance(candidate_answer, str):
        raise ParseError(
            f"Missing or invalid 'candidate_answer' field in synthesis",
            raw_output=raw,
        )

    rationale = parsed.get("rationale")
    if not isinstance(rationale, str):
        raise ParseError(
            f"Missing or invalid 'rationale' field in synthesis",
            raw_output=raw,
        )

    # Extract list fields with defaults
    common_points = _parse_string_list(parsed.get("common_points", []))
    objections = _parse_string_list(parsed.get("objections", []))
    missing = _parse_string_list(parsed.get("missing", []))
    suggested_edits = _parse_string_list(parsed.get("suggested_edits", []))

    return {
        "candidate_answer": candidate_answer,
        "rationale": rationale,
        "common_points": tuple(common_points),
        "objections": tuple(objections),
        "missing": tuple(missing),
        "suggested_edits": tuple(suggested_edits),
    }


def parse_mediator_update(raw: str, strict_json: bool = False) -> dict[str, Any]:
    """Parse mediator update response.

    Args:
        raw: Raw text response from the mediator.
        strict_json: If True, skip recovery and fail on first parse error.

    Returns:
        Dictionary with update fields: candidate_answer, rationale.

    Raises:
        ParseError: If JSON parsing fails or required fields are missing.
    """
    parsed = _parse_json(raw, strict_json)

    # Validate required fields
    candidate_answer = parsed.get("candidate_answer")
    if not isinstance(candidate_answer, str):
        raise ParseError(
            f"Missing or invalid 'candidate_answer' field in update",
            raw_output=raw,
        )

    rationale = parsed.get("rationale")
    if not isinstance(rationale, str):
        raise ParseError(
            f"Missing or invalid 'rationale' field in update",
            raw_output=raw,
        )

    return {
        "candidate_answer": candidate_answer,
        "rationale": rationale,
    }


def _parse_json(raw: str, strict: bool) -> dict[str, Any]:
    """Parse JSON with optional recovery.

    Args:
        raw: Raw text that should contain JSON.
        strict: If True, skip recovery attempts.

    Returns:
        Parsed JSON dictionary.

    Raises:
        ParseError: If all parsing attempts fail.
    """
    # Strategy 1: Direct parse
    try:
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise ParseError(
                f"Expected JSON object, got {type(parsed).__name__}",
                raw_output=raw,
            )
        return parsed
    except json.JSONDecodeError as e:
        if strict:
            raise ParseError(f"JSON parse error: {e}", raw_output=raw) from e

    # Strategy 2: Extract from ```json code block
    try:
        extracted = _extract_json_code_block(raw)
        if extracted:
            parsed = json.loads(extracted)
            if not isinstance(parsed, dict):
                raise ParseError(
                    f"Expected JSON object, got {type(parsed).__name__}",
                    raw_output=raw,
                )
            return parsed
    except json.JSONDecodeError:
        pass

    # Strategy 3: Extract first JSON object with regex
    try:
        extracted = _extract_first_json_object(raw)
        if extracted:
            parsed = json.loads(extracted)
            if not isinstance(parsed, dict):
                raise ParseError(
                    f"Expected JSON object, got {type(parsed).__name__}",
                    raw_output=raw,
                )
            return parsed
    except json.JSONDecodeError:
        pass

    # All strategies failed
    raise ParseError(
        "Failed to parse JSON after all recovery attempts",
        raw_output=raw,
    )


def _extract_json_code_block(text: str) -> str | None:
    """Extract JSON from ```json code fence.

    Args:
        text: Text that may contain a JSON code block.

    Returns:
        Extracted JSON string or None if not found.
    """
    # Match ```json ... ``` or ``` ... ``` with optional language tag
    pattern = r"```(?:json)?\s*\n(.*?)\n```"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def _extract_first_json_object(text: str) -> str | None:
    """Extract the first JSON object from text using regex.

    Args:
        text: Text that may contain a JSON object.

    Returns:
        Extracted JSON string or None if not found.
    """
    # Find the first opening brace
    start = text.find("{")
    if start == -1:
        return None

    # Use a simple brace counting approach to find the matching closing brace
    brace_count = 0
    in_string = False
    escape_next = False

    for i in range(start, len(text)):
        char = text[i]

        if escape_next:
            escape_next = False
            continue

        if char == "\\":
            escape_next = True
            continue

        if char == '"':
            in_string = not in_string
            continue

        if not in_string:
            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0:
                    return text[start : i + 1]

    return None


def _parse_string_list(value: Any) -> list[str]:
    """Parse and validate a list of strings.

    Args:
        value: Value that should be a list of strings.

    Returns:
        List of strings, filtering out non-string values.
    """
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, str)]
