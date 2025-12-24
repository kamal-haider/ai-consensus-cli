"""Tests for JSON parsing with recovery."""

from __future__ import annotations

import pytest

from aicx.prompts.parsing import (
    parse_critique_response,
    parse_mediator_synthesis,
    parse_mediator_update,
    parse_participant_response,
)
from aicx.types import ParseError


# Fixtures: Participant Round 1 responses


@pytest.fixture
def valid_participant_json():
    """Valid participant JSON response."""
    return '{"answer": "The capital of France is Paris.", "confidence": 0.95}'


@pytest.fixture
def participant_json_no_confidence():
    """Participant JSON without optional confidence."""
    return '{"answer": "The capital of France is Paris."}'


@pytest.fixture
def participant_json_in_code_block():
    """Participant JSON wrapped in code fence."""
    return '''```json
{
  "answer": "The capital of France is Paris.",
  "confidence": 0.95
}
```'''


@pytest.fixture
def participant_json_with_markdown():
    """Participant JSON with markdown text before and after."""
    return '''Here is my answer:

{"answer": "The capital of France is Paris.", "confidence": 0.95}

I hope this helps!'''


@pytest.fixture
def participant_invalid_json():
    """Invalid JSON that cannot be recovered."""
    return "This is not JSON at all"


@pytest.fixture
def participant_json_wrong_type():
    """JSON array instead of object."""
    return '["answer", "Paris"]'


@pytest.fixture
def participant_json_missing_answer():
    """JSON missing required answer field."""
    return '{"confidence": 0.95}'


# Fixtures: Critique responses


@pytest.fixture
def valid_critique_json():
    """Valid critique JSON response."""
    return '''{
  "approve": true,
  "critical": false,
  "objections": ["Minor grammar issue"],
  "missing": [],
  "edits": ["Add more detail about history"],
  "confidence": 0.8
}'''


@pytest.fixture
def critique_json_minimal():
    """Critique JSON with minimal required fields."""
    return '''{
  "approve": false,
  "critical": true,
  "objections": ["Factually incorrect"],
  "missing": ["Sources needed"],
  "edits": []
}'''


@pytest.fixture
def critique_json_in_code_block():
    """Critique JSON in code block."""
    return '''```json
{
  "approve": true,
  "critical": false,
  "objections": [],
  "missing": [],
  "edits": []
}
```'''


@pytest.fixture
def critique_json_missing_approve():
    """Critique JSON missing required approve field."""
    return '''{
  "critical": false,
  "objections": [],
  "missing": [],
  "edits": []
}'''


# Fixtures: Mediator synthesis responses


@pytest.fixture
def valid_synthesis_json():
    """Valid mediator synthesis JSON."""
    return '''{
  "candidate_answer": "Paris is the capital of France.",
  "rationale": "All participants agreed on this fact.",
  "common_points": ["Paris is the capital", "Located in France"],
  "objections": [],
  "missing": ["Population data"],
  "suggested_edits": ["Add historical context"]
}'''


@pytest.fixture
def synthesis_json_minimal():
    """Synthesis JSON with minimal required fields."""
    return '''{
  "candidate_answer": "Paris is the capital of France.",
  "rationale": "Consensus reached.",
  "common_points": [],
  "objections": [],
  "missing": [],
  "suggested_edits": []
}'''


@pytest.fixture
def synthesis_json_missing_rationale():
    """Synthesis JSON missing required rationale field."""
    return '''{
  "candidate_answer": "Paris is the capital of France.",
  "common_points": [],
  "objections": [],
  "missing": [],
  "suggested_edits": []
}'''


# Fixtures: Mediator update responses


@pytest.fixture
def valid_update_json():
    """Valid mediator update JSON."""
    return '''{
  "candidate_answer": "Paris is the capital and largest city of France.",
  "rationale": "Added detail about Paris being the largest city based on critique."
}'''


@pytest.fixture
def update_json_missing_candidate():
    """Update JSON missing required candidate_answer field."""
    return '{"rationale": "Updated based on feedback."}'


# Tests: Participant parsing


def test_parse_participant_valid_json(valid_participant_json):
    """Test parsing valid participant JSON."""
    response = parse_participant_response(valid_participant_json, "test-model")
    assert response.model_name == "test-model"
    assert response.answer == "The capital of France is Paris."
    assert response.confidence == 0.95
    assert response.raw == valid_participant_json


def test_parse_participant_no_confidence(participant_json_no_confidence):
    """Test parsing participant JSON without optional confidence."""
    response = parse_participant_response(participant_json_no_confidence, "test-model")
    assert response.answer == "The capital of France is Paris."
    assert response.confidence is None


def test_parse_participant_code_block(participant_json_in_code_block):
    """Test parsing participant JSON from code block."""
    response = parse_participant_response(participant_json_in_code_block, "test-model")
    assert response.answer == "The capital of France is Paris."
    assert response.confidence == 0.95


def test_parse_participant_with_markdown(participant_json_with_markdown):
    """Test parsing participant JSON with surrounding markdown."""
    response = parse_participant_response(participant_json_with_markdown, "test-model")
    assert response.answer == "The capital of France is Paris."
    assert response.confidence == 0.95


def test_parse_participant_strict_mode_fails_on_markdown(participant_json_with_markdown):
    """Test strict mode fails on JSON with markdown."""
    with pytest.raises(ParseError) as exc_info:
        parse_participant_response(participant_json_with_markdown, "test-model", strict_json=True)
    assert "JSON parse error" in str(exc_info.value)


def test_parse_participant_invalid_json(participant_invalid_json):
    """Test parsing invalid JSON raises ParseError."""
    with pytest.raises(ParseError) as exc_info:
        parse_participant_response(participant_invalid_json, "test-model")
    assert "Failed to parse JSON" in str(exc_info.value)


def test_parse_participant_wrong_type(participant_json_wrong_type):
    """Test parsing JSON of wrong type raises ParseError."""
    with pytest.raises(ParseError) as exc_info:
        parse_participant_response(participant_json_wrong_type, "test-model")
    assert "Expected JSON object" in str(exc_info.value)


def test_parse_participant_missing_answer(participant_json_missing_answer):
    """Test parsing JSON missing required answer field."""
    with pytest.raises(ParseError) as exc_info:
        parse_participant_response(participant_json_missing_answer, "test-model")
    assert "answer" in str(exc_info.value)


# Tests: Critique parsing


def test_parse_critique_valid_json(valid_critique_json):
    """Test parsing valid critique JSON."""
    response = parse_critique_response(valid_critique_json, "test-model")
    assert response.model_name == "test-model"
    assert response.approve is True
    assert response.critical is False
    assert response.objections == ("Minor grammar issue",)
    assert response.missing == ()
    assert response.edits == ("Add more detail about history",)
    assert response.confidence == 0.8


def test_parse_critique_minimal(critique_json_minimal):
    """Test parsing critique JSON with minimal fields."""
    response = parse_critique_response(critique_json_minimal, "test-model")
    assert response.approve is False
    assert response.critical is True
    assert response.objections == ("Factually incorrect",)
    assert response.missing == ("Sources needed",)
    assert response.edits == ()
    assert response.confidence is None


def test_parse_critique_code_block(critique_json_in_code_block):
    """Test parsing critique JSON from code block."""
    response = parse_critique_response(critique_json_in_code_block, "test-model")
    assert response.approve is True
    assert response.critical is False


def test_parse_critique_missing_approve(critique_json_missing_approve):
    """Test parsing critique JSON missing required approve field."""
    with pytest.raises(ParseError) as exc_info:
        parse_critique_response(critique_json_missing_approve, "test-model")
    assert "approve" in str(exc_info.value)


# Tests: Mediator synthesis parsing


def test_parse_synthesis_valid_json(valid_synthesis_json):
    """Test parsing valid mediator synthesis JSON."""
    result = parse_mediator_synthesis(valid_synthesis_json)
    assert result["candidate_answer"] == "Paris is the capital of France."
    assert result["rationale"] == "All participants agreed on this fact."
    assert result["common_points"] == ("Paris is the capital", "Located in France")
    assert result["objections"] == ()
    assert result["missing"] == ("Population data",)
    assert result["suggested_edits"] == ("Add historical context",)


def test_parse_synthesis_minimal(synthesis_json_minimal):
    """Test parsing synthesis JSON with minimal fields."""
    result = parse_mediator_synthesis(synthesis_json_minimal)
    assert result["candidate_answer"] == "Paris is the capital of France."
    assert result["rationale"] == "Consensus reached."
    assert result["common_points"] == ()
    assert result["objections"] == ()
    assert result["missing"] == ()
    assert result["suggested_edits"] == ()


def test_parse_synthesis_missing_rationale(synthesis_json_missing_rationale):
    """Test parsing synthesis JSON missing required rationale field."""
    with pytest.raises(ParseError) as exc_info:
        parse_mediator_synthesis(synthesis_json_missing_rationale)
    assert "rationale" in str(exc_info.value)


# Tests: Mediator update parsing


def test_parse_update_valid_json(valid_update_json):
    """Test parsing valid mediator update JSON."""
    result = parse_mediator_update(valid_update_json)
    assert result["candidate_answer"] == "Paris is the capital and largest city of France."
    assert result["rationale"] == "Added detail about Paris being the largest city based on critique."


def test_parse_update_missing_candidate(update_json_missing_candidate):
    """Test parsing update JSON missing required candidate_answer field."""
    with pytest.raises(ParseError) as exc_info:
        parse_mediator_update(update_json_missing_candidate)
    assert "candidate_answer" in str(exc_info.value)


# Tests: Edge cases


def test_parse_nested_json_objects():
    """Test parsing when JSON contains nested objects (should still work)."""
    raw = '{"answer": "Paris", "metadata": {"source": "Wikipedia"}, "confidence": 0.9}'
    response = parse_participant_response(raw, "test-model")
    assert response.answer == "Paris"
    assert response.confidence == 0.9


def test_parse_json_with_escaped_quotes():
    """Test parsing JSON with escaped quotes in strings."""
    raw = r'{"answer": "The \"City of Light\" is Paris.", "confidence": 0.95}'
    response = parse_participant_response(raw, "test-model")
    assert response.answer == 'The "City of Light" is Paris.'


def test_parse_json_with_unicode():
    """Test parsing JSON with unicode characters."""
    raw = '{"answer": "Paris, France \u2013 the capital city", "confidence": 0.95}'
    response = parse_participant_response(raw, "test-model")
    assert "Paris" in response.answer
    assert "\u2013" in response.answer


def test_parse_empty_string_answer():
    """Test that empty string answer is still valid."""
    raw = '{"answer": "", "confidence": 0.5}'
    response = parse_participant_response(raw, "test-model")
    assert response.answer == ""
    assert response.confidence == 0.5


def test_parse_malformed_json_with_trailing_comma():
    """Test parsing JSON with trailing comma (should fail in strict mode)."""
    raw = '{"answer": "Paris", "confidence": 0.95,}'

    # Should fail in strict mode
    with pytest.raises(ParseError):
        parse_participant_response(raw, "test-model", strict_json=True)

    # Should also fail in recovery mode (JSON is truly malformed)
    with pytest.raises(ParseError):
        parse_participant_response(raw, "test-model", strict_json=False)


def test_parse_multiple_json_objects_extracts_first():
    """Test that multiple JSON objects extracts the first one."""
    raw = '''{"answer": "First answer", "confidence": 0.9}
    {"answer": "Second answer", "confidence": 0.8}'''

    response = parse_participant_response(raw, "test-model")
    assert response.answer == "First answer"
    assert response.confidence == 0.9


def test_parse_json_with_newlines_in_strings():
    """Test parsing JSON with newlines in string values."""
    raw = '{"answer": "Line 1\\nLine 2\\nLine 3", "confidence": 0.95}'
    response = parse_participant_response(raw, "test-model")
    assert "Line 1\nLine 2\nLine 3" == response.answer


def test_parse_critique_with_non_string_in_list():
    """Test that non-string values in lists are filtered out."""
    raw = '''{
  "approve": true,
  "critical": false,
  "objections": ["Valid objection", 123, null, "Another valid"],
  "missing": [],
  "edits": []
}'''
    response = parse_critique_response(raw, "test-model")
    # Non-string values should be filtered, only string values kept
    assert response.objections == ("Valid objection", "Another valid")


def test_parse_error_preserves_raw_output():
    """Test that ParseError preserves raw output for debugging."""
    raw = "This is not valid JSON"

    with pytest.raises(ParseError) as exc_info:
        parse_participant_response(raw, "test-model")

    assert exc_info.value.raw_output == raw


def test_parse_code_block_without_language_tag():
    """Test parsing JSON from code block without language tag."""
    raw = '''```
{
  "answer": "Paris is the capital.",
  "confidence": 0.95
}
```'''
    response = parse_participant_response(raw, "test-model")
    assert response.answer == "Paris is the capital."
    assert response.confidence == 0.95


def test_parse_json_with_comments_fails():
    """Test that JSON with comments fails to parse."""
    raw = '''{
  // This is a comment
  "answer": "Paris",
  "confidence": 0.95
}'''

    # JSON doesn't support comments, so this should fail
    with pytest.raises(ParseError):
        parse_participant_response(raw, "test-model")
