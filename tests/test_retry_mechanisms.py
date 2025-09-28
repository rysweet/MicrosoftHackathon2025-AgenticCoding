"""Test suite for retry mechanisms and exponential backoff."""

import asyncio
import pytest
import time
from unittest.mock import Mock, patch

from amplihack.errors import (
    AmplihackError,
    ProcessError,
    SecurityError,
    ValidationError,
    retry_on_error,
    retry_async,
    RetryBudget,
    RetryConfig,
    get_correlation_id,
    set_correlation_id,
    clear_correlation_id,
)


class TestRetryBudget:
    """Test retry budget functionality."""

    def test_budget_initialization(self):
        """Test budget initialization."""
        budget = RetryBudget(max_total_delay=100.0)

        assert budget.max_total_delay == 100.0
        assert budget.used_delay == 0.0
        assert budget.remaining_budget() == 100.0

    def test_budget_consumption(self):
        """Test budget consumption."""
        budget = RetryBudget(max_total_delay=100.0)

        assert budget.can_retry(30.0)
        budget.consume_delay(30.0)

        assert budget.used_delay == 30.0
        assert budget.remaining_budget() == 70.0
        assert budget.can_retry(50.0)
        assert not budget.can_retry(80.0)

    def test_budget_exhaustion(self):
        """Test budget exhaustion."""
        budget = RetryBudget(max_total_delay=50.0)

        budget.consume_delay(40.0)
        assert budget.can_retry(10.0)
        assert not budget.can_retry(15.0)

        budget.consume_delay(10.0)
        assert budget.remaining_budget() == 0.0
        assert not budget.can_retry(1.0)


class TestRetryConfig:
    """Test retry configuration."""

    def test_config_initialization(self):
        """Test configuration initialization with defaults."""
        config = RetryConfig()

        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 30.0
        assert config.exponential_base == 2.0
        assert config.jitter is True
        assert config.budget is not None

    def test_config_validation(self):
        """Test configuration validation."""
        # Valid config
        config = RetryConfig(max_attempts=2, base_delay=0.5, max_delay=10.0)
        assert config.max_attempts == 2

        # Invalid max_attempts
        with pytest.raises(ValueError, match="max_attempts must be at least 1"):
            RetryConfig(max_attempts=0)

        with pytest.raises(ValueError, match="max_attempts cannot exceed 5"):
            RetryConfig(max_attempts=6)

        # Invalid delays
        with pytest.raises(ValueError, match="base_delay must be positive"):
            RetryConfig(base_delay=0)

        with pytest.raises(ValueError, match="max_delay must be >= base_delay"):
            RetryConfig(base_delay=10.0, max_delay=5.0)

        with pytest.raises(ValueError, match="max_delay cannot exceed 30 seconds"):
            RetryConfig(max_delay=35.0)

    def test_delay_calculation(self):
        """Test delay calculation with exponential backoff."""
        config = RetryConfig(
            base_delay=1.0,
            exponential_base=2.0,
            max_delay=10.0,
            jitter=False  # Disable for predictable testing
        )

        assert config.calculate_delay(0) == 0.0
        assert config.calculate_delay(1) == 1.0  # 1.0 * 2^0
        assert config.calculate_delay(2) == 2.0  # 1.0 * 2^1
        assert config.calculate_delay(3) == 4.0  # 1.0 * 2^2
        assert config.calculate_delay(4) == 8.0  # 1.0 * 2^3
        assert config.calculate_delay(5) == 10.0  # Capped at max_delay

    def test_delay_calculation_with_jitter(self):
        """Test delay calculation with jitter."""
        config = RetryConfig(
            base_delay=4.0,
            exponential_base=2.0,
            max_delay=20.0,
            jitter=True
        )

        # With jitter, delay should vary but be within bounds
        delays = [config.calculate_delay(2) for _ in range(10)]
        base_delay = 4.0  # 4.0 * 2^1 = 8.0

        for delay in delays:
            assert 6.0 <= delay <= 10.0  # 8.0 ± 25%
            assert delay >= 0.0

    def test_should_retry_logic(self):
        """Test retry decision logic."""
        config = RetryConfig(max_attempts=3)

        # Test attempt limits
        error = ConnectionError("Network error")
        assert config.should_retry(error, 1)
        assert config.should_retry(error, 2)
        assert not config.should_retry(error, 3)

        # Test non-retryable errors
        validation_error = ValidationError("Invalid input")
        assert not config.should_retry(validation_error, 1)

        security_error = SecurityError("Access denied")
        assert not config.should_retry(security_error, 1)

        # Test retryable errors
        process_error = ProcessError("Command failed")
        assert config.should_retry(process_error, 1)

    def test_custom_error_types(self):
        """Test custom retryable/non-retryable error types."""
        config = RetryConfig(
            retryable_errors=(OSError, IOError),
            non_retryable_errors=(ValueError, TypeError)
        )

        assert config.should_retry(OSError("File error"), 1)
        assert config.should_retry(IOError("IO error"), 1)
        assert not config.should_retry(ValueError("Value error"), 1)
        assert not config.should_retry(TypeError("Type error"), 1)


class TestRetryDecorator:
    """Test retry decorator functionality."""

    def setup_method(self):
        """Setup for each test."""
        clear_correlation_id()

    def teardown_method(self):
        """Cleanup after each test."""
        clear_correlation_id()

    def test_successful_operation_no_retry(self):
        """Test that successful operations don't trigger retries."""
        call_count = 0

        @retry_on_error(RetryConfig(max_attempts=3))
        def successful_operation():
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_operation()

        assert result == "success"
        assert call_count == 1

    def test_retry_on_transient_error(self):
        """Test retry on transient errors."""
        call_count = 0

        @retry_on_error(RetryConfig(max_attempts=3, base_delay=0.01))
        def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Network error")
            return "success"

        result = flaky_operation()

        assert result == "success"
        assert call_count == 3

    def test_retry_exhaustion(self):
        """Test behavior when retries are exhausted."""
        call_count = 0

        @retry_on_error(RetryConfig(max_attempts=2, base_delay=0.01))
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Persistent error")

        with pytest.raises(ConnectionError, match="Persistent error"):
            always_fails()

        assert call_count == 2

    def test_non_retryable_error_no_retry(self):
        """Test that non-retryable errors don't trigger retries."""
        call_count = 0

        @retry_on_error(RetryConfig(max_attempts=3))
        def validation_error_operation():
            nonlocal call_count
            call_count += 1
            raise ValidationError("Invalid input")

        with pytest.raises(ValidationError):
            validation_error_operation()

        assert call_count == 1

    def test_retry_with_correlation_id(self):
        """Test retry with correlation ID tracking."""
        correlation_id = set_correlation_id("test-retry")
        call_count = 0

        @retry_on_error(RetryConfig(max_attempts=2, base_delay=0.01))
        def operation_with_correlation():
            nonlocal call_count
            call_count += 1
            # Verify correlation ID is maintained across retries
            assert get_correlation_id() == "test-retry"
            if call_count == 1:
                raise ConnectionError("First attempt fails")
            return "success"

        result = operation_with_correlation()

        assert result == "success"
        assert call_count == 2
        assert get_correlation_id() == "test-retry"

    def test_retry_budget_enforcement(self):
        """Test that retry budget is enforced."""
        call_count = 0

        # Very small budget that should be exhausted quickly
        config = RetryConfig(
            max_attempts=5,
            base_delay=1.0,
            budget=RetryBudget(max_total_delay=2.0)
        )

        @retry_on_error(config)
        def budget_limited_operation():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Always fails")

        start_time = time.time()

        with pytest.raises(ConnectionError):
            budget_limited_operation()

        elapsed = time.time() - start_time

        # Should stop early due to budget, not reach max_attempts
        assert call_count < 5
        assert elapsed < 5.0  # Much less than what 5 attempts would take

    def test_retry_with_custom_config(self):
        """Test retry with custom configuration."""
        call_count = 0

        custom_config = RetryConfig(
            max_attempts=4,
            base_delay=0.001,
            retryable_errors=(ValueError, OSError),
            non_retryable_errors=()  # Clear default non-retryable errors
        )

        @retry_on_error(custom_config)
        def custom_retry_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Retryable error")
            return "success"

        result = custom_retry_operation()

        assert result == "success"
        assert call_count == 3

    def test_retry_kwargs_config(self):
        """Test retry with configuration via kwargs."""
        call_count = 0

        @retry_on_error(max_attempts=2, base_delay=0.01)
        def kwargs_config_operation():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("First fails")
            return "success"

        result = kwargs_config_operation()

        assert result == "success"
        assert call_count == 2


class TestAsyncRetry:
    """Test async retry functionality."""

    def setup_method(self):
        """Setup for each test."""
        clear_correlation_id()

    def teardown_method(self):
        """Cleanup after each test."""
        clear_correlation_id()

    @pytest.mark.asyncio
    async def test_async_successful_operation(self):
        """Test async operation success without retry."""
        call_count = 0

        @retry_async(RetryConfig(max_attempts=3))
        async def async_success():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.001)
            return "async_success"

        result = await async_success()

        assert result == "async_success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_async_retry_on_error(self):
        """Test async retry on transient errors."""
        call_count = 0

        @retry_async(RetryConfig(max_attempts=3, base_delay=0.01))
        async def async_flaky():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.001)
            if call_count < 3:
                raise ConnectionError("Async network error")
            return "async_success"

        result = await async_flaky()

        assert result == "async_success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_async_retry_exhaustion(self):
        """Test async retry exhaustion."""
        call_count = 0

        @retry_async(RetryConfig(max_attempts=2, base_delay=0.01))
        async def async_always_fails():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.001)
            raise ConnectionError("Async persistent error")

        with pytest.raises(ConnectionError, match="Async persistent error"):
            await async_always_fails()

        assert call_count == 2

    @pytest.mark.asyncio
    async def test_async_correlation_id_tracking(self):
        """Test correlation ID tracking in async retries."""
        correlation_id = set_correlation_id("async-test")
        call_count = 0

        @retry_async(RetryConfig(max_attempts=2, base_delay=0.01))
        async def async_with_correlation():
            nonlocal call_count
            call_count += 1
            # Verify correlation ID is maintained
            assert get_correlation_id() == "async-test"
            await asyncio.sleep(0.001)
            if call_count == 1:
                raise ConnectionError("First async attempt fails")
            return "async_success"

        result = await async_with_correlation()

        assert result == "async_success"
        assert call_count == 2
        assert get_correlation_id() == "async-test"


class TestRetryLogging:
    """Test retry logging functionality."""

    def setup_method(self):
        """Setup for each test."""
        clear_correlation_id()

    def teardown_method(self):
        """Cleanup after each test."""
        clear_correlation_id()

    def test_retry_attempt_logging(self):
        """Test that retry attempts are logged."""
        call_count = 0

        @retry_on_error(RetryConfig(max_attempts=3, base_delay=0.01))
        def logged_retry_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Network error")
            return "success"

        with patch('amplihack.errors.retry.error_logger') as mock_logger:
            result = logged_retry_operation()

            assert result == "success"
            # Should log 2 retry attempts (not the successful final attempt)
            assert mock_logger.log_retry_attempt.call_count == 2

    def test_retry_exhausted_logging(self):
        """Test that retry exhaustion is logged."""
        @retry_on_error(RetryConfig(max_attempts=2, base_delay=0.01))
        def exhausted_operation():
            raise ConnectionError("Persistent error")

        with patch('amplihack.errors.retry.error_logger') as mock_logger:
            with pytest.raises(ConnectionError):
                exhausted_operation()

            # Should log retry exhaustion
            mock_logger.log_retry_exhausted.assert_called_once()

    def test_error_logging_during_retry(self):
        """Test that errors are logged during retry attempts."""
        @retry_on_error(RetryConfig(max_attempts=2, base_delay=0.01))
        def error_logged_operation():
            raise ConnectionError("Network error")

        with patch('amplihack.errors.retry.log_error') as mock_log_error:
            with pytest.raises(ConnectionError):
                error_logged_operation()

            # Should log error for each attempt
            assert mock_log_error.call_count == 2


class TestRetryIntegration:
    """Test retry integration scenarios."""

    def setup_method(self):
        """Setup for each test."""
        clear_correlation_id()

    def teardown_method(self):
        """Cleanup after each test."""
        clear_correlation_id()

    def test_nested_retry_operations(self):
        """Test nested operations with retries."""
        outer_calls = 0
        inner_calls = 0

        @retry_on_error(RetryConfig(max_attempts=2, base_delay=0.01))
        def inner_operation():
            nonlocal inner_calls
            inner_calls += 1
            if inner_calls == 1:
                raise ConnectionError("Inner error")
            return "inner_success"

        @retry_on_error(RetryConfig(max_attempts=2, base_delay=0.01))
        def outer_operation():
            nonlocal outer_calls
            outer_calls += 1
            result = inner_operation()
            if outer_calls == 1:
                raise ProcessError("Outer error")
            return f"outer_success: {result}"

        result = outer_operation()

        assert result == "outer_success: inner_success"
        assert outer_calls == 2
        assert inner_calls == 3  # Called twice from first outer, once from second

    def test_retry_with_exception_chaining(self):
        """Test retry with exception chaining."""
        call_count = 0

        @retry_on_error(RetryConfig(max_attempts=2, base_delay=0.01))
        def chained_exception_operation():
            nonlocal call_count
            call_count += 1
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise ConnectionError("Wrapped error") from e

        with pytest.raises(ConnectionError) as exc_info:
            chained_exception_operation()

        assert call_count == 2
        assert exc_info.value.__cause__ is not None
        assert isinstance(exc_info.value.__cause__, ValueError)

    def test_concurrent_retry_operations(self):
        """Test concurrent operations with retries."""
        import threading
        import queue

        results = queue.Queue()

        @retry_on_error(RetryConfig(max_attempts=2, base_delay=0.01))
        def concurrent_operation(worker_id):
            # Each worker fails once then succeeds
            if not hasattr(concurrent_operation, 'failed_workers'):
                concurrent_operation.failed_workers = set()

            if worker_id not in concurrent_operation.failed_workers:
                concurrent_operation.failed_workers.add(worker_id)
                raise ConnectionError(f"Worker {worker_id} first attempt")

            return f"worker_{worker_id}_success"

        def worker(worker_id):
            try:
                result = concurrent_operation(worker_id)
                results.put(result)
            except Exception as e:
                results.put(f"error: {e}")

        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All workers should succeed after retry
        worker_results = []
        while not results.empty():
            worker_results.append(results.get())

        assert len(worker_results) == 3
        for result in worker_results:
            assert "success" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])