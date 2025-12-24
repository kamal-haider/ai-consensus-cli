"""Tests for logging module."""

from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stderr
from datetime import datetime

import pytest

from aicx import logging


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logging state before and after each test."""
    logging.configure_logging(False)
    yield
    logging.configure_logging(False)


def capture_logs(func):
    """Context manager to capture stderr logs."""
    stderr_capture = io.StringIO()
    with redirect_stderr(stderr_capture):
        func()
    return stderr_capture.getvalue()


def parse_log_lines(output: str) -> list[dict]:
    """Parse JSONL output into list of dicts."""
    if not output.strip():
        return []
    return [json.loads(line) for line in output.strip().split("\n")]


class TestLoggingConfiguration:
    """Tests for logging configuration."""

    def test_default_no_logging(self):
        """By default, no logs should be emitted."""
        output = capture_logs(
            lambda: logging.log_event("test_event", payload={"key": "value"})
        )
        assert output == ""

    def test_verbose_enables_logging(self):
        """Verbose mode should enable logging."""
        logging.configure_logging(True)
        output = capture_logs(
            lambda: logging.log_event("test_event", payload={"key": "value"})
        )
        assert output != ""
        logs = parse_log_lines(output)
        assert len(logs) == 1
        assert logs[0]["event"] == "test_event"

    def test_can_disable_after_enable(self):
        """Should be able to disable logging after enabling."""
        logging.configure_logging(True)
        logging.configure_logging(False)
        output = capture_logs(
            lambda: logging.log_event("test_event", payload={"key": "value"})
        )
        assert output == ""


class TestLogEventStructure:
    """Tests for log event structure."""

    def test_minimal_event(self):
        """Test minimal event with only required fields."""
        logging.configure_logging(True)
        output = capture_logs(lambda: logging.log_event("test_event"))
        logs = parse_log_lines(output)

        assert len(logs) == 1
        log = logs[0]

        # Required fields
        assert log["event"] == "test_event"
        assert "timestamp" in log
        assert log["payload"] == {}

        # Optional fields should not be present
        assert "round" not in log
        assert "model" not in log

    def test_event_with_all_fields(self):
        """Test event with all optional fields."""
        logging.configure_logging(True)
        output = capture_logs(
            lambda: logging.log_event(
                "test_event",
                payload={"key": "value"},
                round_index=2,
                model="gpt-4",
            )
        )
        logs = parse_log_lines(output)

        assert len(logs) == 1
        log = logs[0]

        assert log["event"] == "test_event"
        assert log["round"] == 2
        assert log["model"] == "gpt-4"
        assert log["payload"]["key"] == "value"

    def test_timestamp_format(self):
        """Test that timestamp is in ISO 8601 UTC format."""
        logging.configure_logging(True)
        output = capture_logs(lambda: logging.log_event("test_event"))
        logs = parse_log_lines(output)

        timestamp = logs[0]["timestamp"]
        # Should parse as ISO format
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert dt is not None
        # Should have timezone info
        assert timestamp.endswith("+00:00") or timestamp.endswith("Z")

    def test_stable_key_ordering(self):
        """Test that JSON keys are sorted for deterministic output."""
        logging.configure_logging(True)
        output = capture_logs(
            lambda: logging.log_event(
                "test_event",
                payload={"z": 1, "a": 2, "m": 3},
                round_index=1,
                model="test",
            )
        )

        # Parse the raw line to check key ordering
        line = output.strip()
        parsed = json.loads(line)

        # Verify it's valid JSON
        assert parsed["event"] == "test_event"

        # Check that the line has sorted keys by verifying payload keys are sorted
        payload_start = line.index('"payload"')
        payload_section = line[payload_start:]
        # Keys should appear in alphabetical order: a, m, z
        assert payload_section.index('"a"') < payload_section.index('"m"')
        assert payload_section.index('"m"') < payload_section.index('"z"')


class TestSecretRedaction:
    """Tests for secret redaction."""

    def test_redact_api_key(self):
        """Test redaction of API keys."""
        logging.configure_logging(True)
        output = capture_logs(
            lambda: logging.log_event(
                "test_event",
                payload={"config": "api_key=sk-1234567890abcdef"},
            )
        )
        logs = parse_log_lines(output)

        assert "sk-1234567890abcdef" not in logs[0]["payload"]["config"]
        assert "[REDACTED]" in logs[0]["payload"]["config"]

    def test_redact_openai_api_key(self):
        """Test redaction of OPENAI_API_KEY."""
        logging.configure_logging(True)
        output = capture_logs(
            lambda: logging.log_event(
                "test_event",
                payload={"env": "OPENAI_API_KEY=sk-proj-abc123"},
            )
        )
        logs = parse_log_lines(output)

        assert "sk-proj-abc123" not in logs[0]["payload"]["env"]
        assert "[REDACTED]" in logs[0]["payload"]["env"]

    def test_redact_anthropic_api_key(self):
        """Test redaction of ANTHROPIC_API_KEY."""
        logging.configure_logging(True)
        output = capture_logs(
            lambda: logging.log_event(
                "test_event",
                payload={"env": "ANTHROPIC_API_KEY=sk-ant-xyz789"},
            )
        )
        logs = parse_log_lines(output)

        assert "sk-ant-xyz789" not in logs[0]["payload"]["env"]
        assert "[REDACTED]" in logs[0]["payload"]["env"]

    def test_redact_gemini_api_key(self):
        """Test redaction of GEMINI_API_KEY."""
        logging.configure_logging(True)
        output = capture_logs(
            lambda: logging.log_event(
                "test_event",
                payload={"env": "GEMINI_API_KEY=AIzaSyDaGmWKa4JsXMYxY"},
            )
        )
        logs = parse_log_lines(output)

        assert "AIzaSyDaGmWKa4JsXMYxY" not in logs[0]["payload"]["env"]
        assert "[REDACTED]" in logs[0]["payload"]["env"]

    def test_redact_bearer_token(self):
        """Test redaction of bearer tokens."""
        logging.configure_logging(True)
        output = capture_logs(
            lambda: logging.log_event(
                "test_event",
                payload={"auth": "Bearer abc123xyz"},
            )
        )
        logs = parse_log_lines(output)

        assert "abc123xyz" not in logs[0]["payload"]["auth"]
        assert "[REDACTED]" in logs[0]["payload"]["auth"]

    def test_redact_nested_secrets(self):
        """Test redaction in nested structures."""
        logging.configure_logging(True)
        output = capture_logs(
            lambda: logging.log_event(
                "test_event",
                payload={
                    "config": {
                        "providers": {
                            "openai": {"api_key": "sk-secret123"},
                        },
                    },
                },
            )
        )
        logs = parse_log_lines(output)

        config = logs[0]["payload"]["config"]
        assert "sk-secret123" not in str(config)
        assert "[REDACTED]" in config["providers"]["openai"]["api_key"]

    def test_redact_in_lists(self):
        """Test redaction in list structures."""
        logging.configure_logging(True)
        output = capture_logs(
            lambda: logging.log_event(
                "test_event",
                payload={"keys": ["api_key=secret1", "token: secret2"]},
            )
        )
        logs = parse_log_lines(output)

        keys = logs[0]["payload"]["keys"]
        assert "secret1" not in str(keys)
        assert "secret2" not in str(keys)
        assert all("[REDACTED]" in k for k in keys)

    def test_preserve_non_secrets(self):
        """Test that non-secret data is preserved."""
        logging.configure_logging(True)
        output = capture_logs(
            lambda: logging.log_event(
                "test_event",
                payload={
                    "user_prompt": "What is the capital of France?",
                    "model": "gpt-4",
                    "temperature": 0.7,
                },
            )
        )
        logs = parse_log_lines(output)

        payload = logs[0]["payload"]
        assert payload["user_prompt"] == "What is the capital of France?"
        assert payload["model"] == "gpt-4"
        assert payload["temperature"] == 0.7


class TestSpecificEvents:
    """Tests for specific event logging functions."""

    def test_log_config_loaded(self):
        """Test config_loaded event."""
        logging.configure_logging(True)
        config = {"models": ["gpt-4", "claude-3"], "max_rounds": 3}
        output = capture_logs(lambda: logging.log_config_loaded(config))
        logs = parse_log_lines(output)

        assert len(logs) == 1
        assert logs[0]["event"] == "config_loaded"
        assert logs[0]["payload"]["config"] == config

    def test_log_round_started(self):
        """Test round_started event."""
        logging.configure_logging(True)
        output = capture_logs(lambda: logging.log_round_started(0, 3))
        logs = parse_log_lines(output)

        assert len(logs) == 1
        assert logs[0]["event"] == "round_started"
        assert logs[0]["round"] == 0
        assert logs[0]["payload"]["num_participants"] == 3

    def test_log_model_request(self):
        """Test model_request event."""
        logging.configure_logging(True)
        output = capture_logs(
            lambda: logging.log_model_request(
                model="gpt-4",
                round_index=1,
                prompt_length=150,
                has_candidate=True,
            )
        )
        logs = parse_log_lines(output)

        assert len(logs) == 1
        assert logs[0]["event"] == "model_request"
        assert logs[0]["model"] == "gpt-4"
        assert logs[0]["round"] == 1
        assert logs[0]["payload"]["prompt_length"] == 150
        assert logs[0]["payload"]["has_candidate"] is True

    def test_log_model_response_round1(self):
        """Test model_response event for round 1 (no approval/critical)."""
        logging.configure_logging(True)
        output = capture_logs(
            lambda: logging.log_model_response(
                model="claude-3",
                round_index=0,
                response_length=250,
            )
        )
        logs = parse_log_lines(output)

        assert len(logs) == 1
        assert logs[0]["event"] == "model_response"
        assert logs[0]["model"] == "claude-3"
        assert logs[0]["round"] == 0
        assert logs[0]["payload"]["response_length"] == 250
        assert "approve" not in logs[0]["payload"]
        assert "critical" not in logs[0]["payload"]

    def test_log_model_response_round2_plus(self):
        """Test model_response event for round 2+ (with approval/critical)."""
        logging.configure_logging(True)
        output = capture_logs(
            lambda: logging.log_model_response(
                model="gpt-4",
                round_index=1,
                response_length=180,
                approve=True,
                critical=False,
            )
        )
        logs = parse_log_lines(output)

        assert len(logs) == 1
        assert logs[0]["payload"]["approve"] is True
        assert logs[0]["payload"]["critical"] is False

    def test_log_parse_recovery_attempt(self):
        """Test parse_recovery_attempt event."""
        logging.configure_logging(True)
        output = capture_logs(
            lambda: logging.log_parse_recovery_attempt(
                model="gpt-4",
                round_index=1,
                error="Missing 'approve' field",
                strategy="assume_approve_false",
            )
        )
        logs = parse_log_lines(output)

        assert len(logs) == 1
        assert logs[0]["event"] == "parse_recovery_attempt"
        assert logs[0]["model"] == "gpt-4"
        assert logs[0]["round"] == 1
        assert logs[0]["payload"]["error"] == "Missing 'approve' field"
        assert logs[0]["payload"]["strategy"] == "assume_approve_false"

    def test_log_context_truncated(self):
        """Test context_truncated event."""
        logging.configure_logging(True)
        output = capture_logs(
            lambda: logging.log_context_truncated(
                model="claude-3",
                round_index=2,
                original_tokens=5000,
                truncated_tokens=4000,
            )
        )
        logs = parse_log_lines(output)

        assert len(logs) == 1
        assert logs[0]["event"] == "context_truncated"
        assert logs[0]["model"] == "claude-3"
        assert logs[0]["round"] == 2
        assert logs[0]["payload"]["original_tokens"] == 5000
        assert logs[0]["payload"]["truncated_tokens"] == 4000

    def test_log_mediator_update(self):
        """Test mediator_update event."""
        logging.configure_logging(True)
        output = capture_logs(
            lambda: logging.log_mediator_update(
                round_index=1,
                candidate_length=320,
                approval_count=2,
                critical_count=0,
            )
        )
        logs = parse_log_lines(output)

        assert len(logs) == 1
        assert logs[0]["event"] == "mediator_update"
        assert logs[0]["round"] == 1
        assert logs[0]["payload"]["candidate_length"] == 320
        assert logs[0]["payload"]["approval_count"] == 2
        assert logs[0]["payload"]["critical_count"] == 0

    def test_log_consensus_check(self):
        """Test consensus_check event."""
        logging.configure_logging(True)
        output = capture_logs(
            lambda: logging.log_consensus_check(
                round_index=2,
                consensus_reached=True,
                approval_ratio=0.75,
                required_ratio=0.67,
                critical_count=0,
            )
        )
        logs = parse_log_lines(output)

        assert len(logs) == 1
        assert logs[0]["event"] == "consensus_check"
        assert logs[0]["round"] == 2
        assert logs[0]["payload"]["consensus_reached"] is True
        assert logs[0]["payload"]["approval_ratio"] == 0.75
        assert logs[0]["payload"]["required_ratio"] == 0.67
        assert logs[0]["payload"]["critical_count"] == 0

    def test_log_run_complete(self):
        """Test run_complete event."""
        logging.configure_logging(True)
        output = capture_logs(
            lambda: logging.log_run_complete(
                rounds_completed=2,
                consensus_reached=True,
                exit_code=0,
            )
        )
        logs = parse_log_lines(output)

        assert len(logs) == 1
        assert logs[0]["event"] == "run_complete"
        assert logs[0]["payload"]["rounds_completed"] == 2
        assert logs[0]["payload"]["consensus_reached"] is True
        assert logs[0]["payload"]["exit_code"] == 0

    def test_log_error(self):
        """Test error event."""
        logging.configure_logging(True)
        output = capture_logs(
            lambda: logging.log_error(
                error_type="ProviderError",
                message="Connection timeout",
                round_index=1,
                model="gpt-4",
            )
        )
        logs = parse_log_lines(output)

        assert len(logs) == 1
        assert logs[0]["event"] == "error"
        assert logs[0]["round"] == 1
        assert logs[0]["model"] == "gpt-4"
        assert logs[0]["payload"]["error_type"] == "ProviderError"
        assert logs[0]["payload"]["message"] == "Connection timeout"

    def test_log_error_minimal(self):
        """Test error event without optional fields."""
        logging.configure_logging(True)
        output = capture_logs(
            lambda: logging.log_error(
                error_type="ConfigError",
                message="Invalid config",
            )
        )
        logs = parse_log_lines(output)

        assert len(logs) == 1
        assert logs[0]["event"] == "error"
        assert "round" not in logs[0]
        assert "model" not in logs[0]
        assert logs[0]["payload"]["error_type"] == "ConfigError"


class TestMultipleEvents:
    """Tests for logging multiple events."""

    def test_multiple_events_in_sequence(self):
        """Test that multiple events are logged as separate lines."""
        logging.configure_logging(True)

        def log_multiple():
            logging.log_round_started(0, 3)
            logging.log_model_request("gpt-4", 0, 100, False)
            logging.log_model_response("gpt-4", 0, 200)

        output = capture_logs(log_multiple)
        logs = parse_log_lines(output)

        assert len(logs) == 3
        assert logs[0]["event"] == "round_started"
        assert logs[1]["event"] == "model_request"
        assert logs[2]["event"] == "model_response"

    def test_events_maintain_order(self):
        """Test that events maintain the order they were logged."""
        logging.configure_logging(True)

        def log_sequence():
            for i in range(5):
                logging.log_event(f"event_{i}", payload={"index": i})

        output = capture_logs(log_sequence)
        logs = parse_log_lines(output)

        assert len(logs) == 5
        for i, log in enumerate(logs):
            assert log["event"] == f"event_{i}"
            assert log["payload"]["index"] == i


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_payload(self):
        """Test event with explicit empty payload."""
        logging.configure_logging(True)
        output = capture_logs(lambda: logging.log_event("test_event", payload={}))
        logs = parse_log_lines(output)

        assert logs[0]["payload"] == {}

    def test_none_payload(self):
        """Test event with None payload."""
        logging.configure_logging(True)
        output = capture_logs(lambda: logging.log_event("test_event", payload=None))
        logs = parse_log_lines(output)

        assert logs[0]["payload"] == {}

    def test_complex_nested_payload(self):
        """Test event with deeply nested payload."""
        logging.configure_logging(True)
        complex_payload = {
            "level1": {
                "level2": {
                    "level3": {
                        "data": [1, 2, 3],
                        "nested_list": [{"a": 1}, {"b": 2}],
                    }
                }
            }
        }
        output = capture_logs(
            lambda: logging.log_event("test_event", payload=complex_payload)
        )
        logs = parse_log_lines(output)

        assert logs[0]["payload"] == complex_payload

    def test_round_zero(self):
        """Test that round 0 is properly logged (not confused with None)."""
        logging.configure_logging(True)
        output = capture_logs(
            lambda: logging.log_event("test_event", round_index=0)
        )
        logs = parse_log_lines(output)

        assert "round" in logs[0]
        assert logs[0]["round"] == 0

    def test_special_characters_in_payload(self):
        """Test that special characters are properly escaped in JSON."""
        logging.configure_logging(True)
        output = capture_logs(
            lambda: logging.log_event(
                "test_event",
                payload={"text": 'Line 1\nLine 2\t"quoted"\r\nLine 3'},
            )
        )
        logs = parse_log_lines(output)

        assert logs[0]["payload"]["text"] == 'Line 1\nLine 2\t"quoted"\r\nLine 3'

    def test_unicode_in_payload(self):
        """Test that unicode characters are handled correctly."""
        logging.configure_logging(True)
        output = capture_logs(
            lambda: logging.log_event(
                "test_event",
                payload={"text": "Hello 世界 🌍"},
            )
        )
        logs = parse_log_lines(output)

        assert logs[0]["payload"]["text"] == "Hello 世界 🌍"
