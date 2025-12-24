"""Tests for retry policy."""

from __future__ import annotations

import time
from unittest.mock import Mock

import pytest

from aicx.retry import (
    NON_RETRYABLE_CODES,
    RETRYABLE_CODES,
    RetryableProvider,
    calculate_delay,
    execute_with_retry,
    get_retry_after,
    is_retryable,
    wrap_with_retry,
)
from aicx.types import PromptRequest, ProviderError, Response, RetryConfig, Role


class TestRetryConfig:
    """Tests for RetryConfig validation."""

    def test_default_retry_config(self):
        """Test default RetryConfig values."""
        config = RetryConfig()

        assert config.max_retries == 2
        assert config.base_delay_seconds == 1.0
        assert config.max_delay_seconds == 30.0
        assert config.exponential_base == 2.0
        assert config.jitter is True

    def test_custom_retry_config(self):
        """Test custom RetryConfig values."""
        config = RetryConfig(
            max_retries=5,
            base_delay_seconds=0.5,
            max_delay_seconds=60.0,
            exponential_base=3.0,
            jitter=False,
        )

        assert config.max_retries == 5
        assert config.base_delay_seconds == 0.5
        assert config.max_delay_seconds == 60.0
        assert config.exponential_base == 3.0
        assert config.jitter is False

    def test_negative_max_retries_raises_error(self):
        """Test that negative max_retries raises ValueError."""
        with pytest.raises(ValueError, match="max_retries must be >= 0"):
            RetryConfig(max_retries=-1)

    def test_zero_base_delay_raises_error(self):
        """Test that zero base_delay_seconds raises ValueError."""
        with pytest.raises(ValueError, match="base_delay_seconds must be > 0"):
            RetryConfig(base_delay_seconds=0.0)

    def test_negative_base_delay_raises_error(self):
        """Test that negative base_delay_seconds raises ValueError."""
        with pytest.raises(ValueError, match="base_delay_seconds must be > 0"):
            RetryConfig(base_delay_seconds=-1.0)

    def test_zero_max_delay_raises_error(self):
        """Test that zero max_delay_seconds raises ValueError."""
        with pytest.raises(ValueError, match="max_delay_seconds must be > 0"):
            RetryConfig(max_delay_seconds=0.0)

    def test_negative_max_delay_raises_error(self):
        """Test that negative max_delay_seconds raises ValueError."""
        with pytest.raises(ValueError, match="max_delay_seconds must be > 0"):
            RetryConfig(max_delay_seconds=-1.0)

    def test_zero_exponential_base_raises_error(self):
        """Test that zero exponential_base raises ValueError."""
        with pytest.raises(ValueError, match="exponential_base must be > 0"):
            RetryConfig(exponential_base=0.0)

    def test_negative_exponential_base_raises_error(self):
        """Test that negative exponential_base raises ValueError."""
        with pytest.raises(ValueError, match="exponential_base must be > 0"):
            RetryConfig(exponential_base=-1.0)


class TestErrorClassification:
    """Tests for error classification."""

    def test_retryable_codes_set(self):
        """Test that RETRYABLE_CODES contains expected values."""
        assert "timeout" in RETRYABLE_CODES
        assert "network" in RETRYABLE_CODES
        assert "rate_limit" in RETRYABLE_CODES
        assert "service_unavailable" in RETRYABLE_CODES

    def test_non_retryable_codes_set(self):
        """Test that NON_RETRYABLE_CODES contains expected values."""
        assert "auth" in NON_RETRYABLE_CODES
        assert "config" in NON_RETRYABLE_CODES
        assert "api_error" in NON_RETRYABLE_CODES

    def test_is_retryable_with_timeout_error(self):
        """Test that timeout errors are retryable."""
        error = ProviderError("Timeout", provider="test", code="timeout")
        assert is_retryable(error) is True

    def test_is_retryable_with_network_error(self):
        """Test that network errors are retryable."""
        error = ProviderError("Network error", provider="test", code="network")
        assert is_retryable(error) is True

    def test_is_retryable_with_rate_limit_error(self):
        """Test that rate limit errors are retryable."""
        error = ProviderError("Rate limited", provider="test", code="rate_limit")
        assert is_retryable(error) is True

    def test_is_retryable_with_service_unavailable_error(self):
        """Test that service unavailable errors are retryable."""
        error = ProviderError(
            "Service unavailable", provider="test", code="service_unavailable"
        )
        assert is_retryable(error) is True

    def test_is_not_retryable_with_auth_error(self):
        """Test that auth errors are not retryable."""
        error = ProviderError("Auth failed", provider="test", code="auth")
        assert is_retryable(error) is False

    def test_is_not_retryable_with_config_error(self):
        """Test that config errors are not retryable."""
        error = ProviderError("Config error", provider="test", code="config")
        assert is_retryable(error) is False

    def test_is_not_retryable_with_api_error(self):
        """Test that API errors are not retryable."""
        error = ProviderError("API error", provider="test", code="api_error")
        assert is_retryable(error) is False

    def test_is_not_retryable_with_no_code(self):
        """Test that errors with no code are not retryable."""
        error = ProviderError("Unknown error", provider="test", code=None)
        assert is_retryable(error) is False

    def test_get_retry_after_returns_none(self):
        """Test that get_retry_after returns None (v1 limitation)."""
        error = ProviderError("Rate limited", provider="test", code="rate_limit")
        assert get_retry_after(error) is None


class TestDelayCalculation:
    """Tests for delay calculation."""

    def test_calculate_delay_first_attempt(self):
        """Test delay calculation for first retry attempt."""
        config = RetryConfig(
            base_delay_seconds=1.0, exponential_base=2.0, jitter=False
        )
        delay = calculate_delay(0, config)
        assert delay == 1.0  # 1.0 * (2.0 ** 0) = 1.0

    def test_calculate_delay_second_attempt(self):
        """Test delay calculation for second retry attempt."""
        config = RetryConfig(
            base_delay_seconds=1.0, exponential_base=2.0, jitter=False
        )
        delay = calculate_delay(1, config)
        assert delay == 2.0  # 1.0 * (2.0 ** 1) = 2.0

    def test_calculate_delay_third_attempt(self):
        """Test delay calculation for third retry attempt."""
        config = RetryConfig(
            base_delay_seconds=1.0, exponential_base=2.0, jitter=False
        )
        delay = calculate_delay(2, config)
        assert delay == 4.0  # 1.0 * (2.0 ** 2) = 4.0

    def test_calculate_delay_capped_at_max(self):
        """Test that delay is capped at max_delay_seconds."""
        config = RetryConfig(
            base_delay_seconds=1.0,
            exponential_base=2.0,
            max_delay_seconds=5.0,
            jitter=False,
        )
        delay = calculate_delay(10, config)  # Would be 1024.0 without cap
        assert delay == 5.0

    def test_calculate_delay_with_jitter(self):
        """Test that jitter adds randomness to delay."""
        config = RetryConfig(
            base_delay_seconds=1.0, exponential_base=2.0, jitter=True
        )

        # Run multiple times to verify jitter adds variance
        delays = [calculate_delay(1, config) for _ in range(10)]

        # Base delay is 2.0, jitter adds 0-25% (0 to 0.5)
        # So delays should be in range [2.0, 2.5]
        for delay in delays:
            assert 2.0 <= delay <= 2.5

        # With 10 samples, very likely to have different values
        assert len(set(delays)) > 1

    def test_calculate_delay_custom_exponential_base(self):
        """Test delay calculation with custom exponential base."""
        config = RetryConfig(
            base_delay_seconds=0.5, exponential_base=3.0, jitter=False
        )
        delay = calculate_delay(2, config)
        assert delay == 4.5  # 0.5 * (3.0 ** 2) = 4.5


class TestRetryExecution:
    """Tests for retry execution logic."""

    def test_execute_with_retry_success_first_attempt(self):
        """Test successful execution on first attempt."""
        mock_fn = Mock(return_value="success")
        config = RetryConfig(max_retries=2)

        result = execute_with_retry(mock_fn, config, "test-provider")

        assert result == "success"
        assert mock_fn.call_count == 1

    def test_execute_with_retry_success_after_one_retry(self):
        """Test successful execution after one retry."""
        mock_fn = Mock(
            side_effect=[
                ProviderError("Timeout", provider="test", code="timeout"),
                "success",
            ]
        )
        config = RetryConfig(max_retries=2, base_delay_seconds=0.01, jitter=False)

        start_time = time.time()
        result = execute_with_retry(mock_fn, config, "test-provider")
        elapsed = time.time() - start_time

        assert result == "success"
        assert mock_fn.call_count == 2
        # Should have slept for ~0.01 seconds (first retry delay)
        assert elapsed >= 0.01

    def test_execute_with_retry_success_after_two_retries(self):
        """Test successful execution after two retries."""
        mock_fn = Mock(
            side_effect=[
                ProviderError("Network error", provider="test", code="network"),
                ProviderError("Timeout", provider="test", code="timeout"),
                "success",
            ]
        )
        config = RetryConfig(max_retries=2, base_delay_seconds=0.01, jitter=False)

        start_time = time.time()
        result = execute_with_retry(mock_fn, config, "test-provider")
        elapsed = time.time() - start_time

        assert result == "success"
        assert mock_fn.call_count == 3
        # Should have slept for ~0.01 + ~0.02 = ~0.03 seconds
        assert elapsed >= 0.03

    def test_execute_with_retry_fails_after_max_retries(self):
        """Test that execution fails after max retries exhausted."""
        mock_fn = Mock(
            side_effect=ProviderError("Timeout", provider="test", code="timeout")
        )
        config = RetryConfig(max_retries=2, base_delay_seconds=0.01, jitter=False)

        with pytest.raises(ProviderError, match="Timeout"):
            execute_with_retry(mock_fn, config, "test-provider")

        # Should attempt: initial + 2 retries = 3 total
        assert mock_fn.call_count == 3

    def test_execute_with_retry_non_retryable_error_not_retried(self):
        """Test that non-retryable errors are not retried."""
        mock_fn = Mock(
            side_effect=ProviderError("Auth failed", provider="test", code="auth")
        )
        config = RetryConfig(max_retries=2)

        with pytest.raises(ProviderError, match="Auth failed"):
            execute_with_retry(mock_fn, config, "test-provider")

        # Should only attempt once (no retries for auth errors)
        assert mock_fn.call_count == 1

    def test_execute_with_retry_zero_max_retries(self):
        """Test execution with zero max_retries (no retries)."""
        mock_fn = Mock(
            side_effect=ProviderError("Timeout", provider="test", code="timeout")
        )
        config = RetryConfig(max_retries=0)

        with pytest.raises(ProviderError, match="Timeout"):
            execute_with_retry(mock_fn, config, "test-provider")

        # Should only attempt once (max_retries=0 means no retries)
        assert mock_fn.call_count == 1


class TestRetryableProvider:
    """Tests for RetryableProvider wrapper."""

    def test_retryable_provider_wraps_name(self):
        """Test that RetryableProvider exposes wrapped provider name."""
        mock_adapter = Mock()
        mock_adapter.name = "test-provider"
        config = RetryConfig()

        wrapper = RetryableProvider(mock_adapter, config)

        assert wrapper.name == "test-provider"

    def test_retryable_provider_wraps_supports_json(self):
        """Test that RetryableProvider exposes wrapped provider supports_json."""
        mock_adapter = Mock()
        mock_adapter.supports_json = True
        config = RetryConfig()

        wrapper = RetryableProvider(mock_adapter, config)

        assert wrapper.supports_json is True

    def test_retryable_provider_successful_call(self):
        """Test successful call through RetryableProvider."""
        mock_adapter = Mock()
        mock_adapter.name = "test-provider"
        mock_response = Response(model_name="test", answer="success")
        mock_adapter.create_chat_completion = Mock(return_value=mock_response)

        config = RetryConfig()
        wrapper = RetryableProvider(mock_adapter, config)

        request = PromptRequest(
            user_prompt="test",
            system_prompt="test",
            round_index=0,
            role=Role.PARTICIPANT,
        )
        result = wrapper.create_chat_completion(request)

        assert result == mock_response
        assert mock_adapter.create_chat_completion.call_count == 1

    def test_retryable_provider_retries_on_failure(self):
        """Test that RetryableProvider retries on retryable failure."""
        mock_adapter = Mock()
        mock_adapter.name = "test-provider"
        mock_response = Response(model_name="test", answer="success")
        mock_adapter.create_chat_completion = Mock(
            side_effect=[
                ProviderError("Timeout", provider="test", code="timeout"),
                mock_response,
            ]
        )

        config = RetryConfig(base_delay_seconds=0.01, jitter=False)
        wrapper = RetryableProvider(mock_adapter, config)

        request = PromptRequest(
            user_prompt="test",
            system_prompt="test",
            round_index=0,
            role=Role.PARTICIPANT,
        )
        result = wrapper.create_chat_completion(request)

        assert result == mock_response
        assert mock_adapter.create_chat_completion.call_count == 2

    def test_retryable_provider_fails_after_max_retries(self):
        """Test that RetryableProvider fails after max retries."""
        mock_adapter = Mock()
        mock_adapter.name = "test-provider"
        mock_adapter.create_chat_completion = Mock(
            side_effect=ProviderError("Timeout", provider="test", code="timeout")
        )

        config = RetryConfig(max_retries=2, base_delay_seconds=0.01, jitter=False)
        wrapper = RetryableProvider(mock_adapter, config)

        request = PromptRequest(
            user_prompt="test",
            system_prompt="test",
            round_index=0,
            role=Role.PARTICIPANT,
        )

        with pytest.raises(ProviderError, match="Timeout"):
            wrapper.create_chat_completion(request)

        assert mock_adapter.create_chat_completion.call_count == 3


class TestWrapWithRetry:
    """Tests for wrap_with_retry function."""

    def test_wrap_with_retry_none_config_returns_original(self):
        """Test that wrap_with_retry returns original adapter when config is None."""
        mock_adapter = Mock()

        result = wrap_with_retry(mock_adapter, None)

        assert result is mock_adapter

    def test_wrap_with_retry_returns_wrapped_adapter(self):
        """Test that wrap_with_retry returns RetryableProvider when config provided."""
        mock_adapter = Mock()
        mock_adapter.name = "test-provider"
        mock_adapter.supports_json = True
        config = RetryConfig()

        result = wrap_with_retry(mock_adapter, config)

        assert isinstance(result, RetryableProvider)
        assert result.name == "test-provider"
        assert result.supports_json is True

    def test_wrap_with_retry_wrapped_adapter_works(self):
        """Test that wrapped adapter works correctly."""
        mock_adapter = Mock()
        mock_adapter.name = "test-provider"
        mock_response = Response(model_name="test", answer="success")
        mock_adapter.create_chat_completion = Mock(return_value=mock_response)

        config = RetryConfig()
        wrapper = wrap_with_retry(mock_adapter, config)

        request = PromptRequest(
            user_prompt="test",
            system_prompt="test",
            round_index=0,
            role=Role.PARTICIPANT,
        )
        result = wrapper.create_chat_completion(request)

        assert result == mock_response
        assert mock_adapter.create_chat_completion.call_count == 1
