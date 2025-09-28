"""Comprehensive tests for rate limiting system."""

import asyncio
import threading
import time

import pytest

from src.amplihack.rate_limiter import (
    AdaptiveBackoff,
    ExponentialBackoff,
    ProgressUpdate,
    RateLimitConfig,
    RateLimiter,
    RateLimitExhausted,
    RateLimitState,
    SlidingWindowCounter,
    TokenBucket,
    TokenBudgetExceeded,
    rate_limit,
)


class TestRateLimitConfig:
    """Test configuration validation."""

    def test_default_config(self):
        """Test default configuration values."""
        config = RateLimitConfig()
        assert config.initial_tokens == 1000
        assert config.refill_rate == 100.0
        assert config.max_retries == 5
        assert config.initial_delay == 1.0
        assert config.max_delay == 60.0
        assert config.jitter_factor == 0.1
        assert config.backoff_multiplier == 2.0

    def test_custom_config(self):
        """Test custom configuration."""
        config = RateLimitConfig(
            initial_tokens=500,
            refill_rate=50.0,
            max_retries=3,
            initial_delay=2.0,
            max_delay=30.0,
            jitter_factor=0.2,
            backoff_multiplier=1.5,
        )
        assert config.initial_tokens == 500
        assert config.refill_rate == 50.0
        assert config.max_retries == 3

    def test_invalid_config(self):
        """Test configuration validation."""
        with pytest.raises(ValueError, match="initial_tokens must be positive"):
            RateLimitConfig(initial_tokens=0)

        with pytest.raises(ValueError, match="refill_rate must be positive"):
            RateLimitConfig(refill_rate=-1)

        with pytest.raises(ValueError, match="max_delay must be >= initial_delay"):
            RateLimitConfig(initial_delay=10, max_delay=5)

        with pytest.raises(ValueError, match="jitter_factor must be in range"):
            RateLimitConfig(jitter_factor=1.5)


class TestExponentialBackoff:
    """Test exponential backoff implementation."""

    def test_calculate_delay_no_retry(self):
        """Test delay calculation with no retries."""
        config = RateLimitConfig()
        backoff = ExponentialBackoff(config)
        state = RateLimitState(current_tokens=100, last_refill=None)

        delay = backoff.calculate_delay(state)
        assert delay == 0.0

    def test_calculate_delay_with_retries(self):
        """Test exponential delay calculation."""
        config = RateLimitConfig(initial_delay=1.0, backoff_multiplier=2.0, jitter_factor=0)
        backoff = ExponentialBackoff(config)
        state = RateLimitState(current_tokens=100, last_refill=None)

        # First retry: 1 second
        state.retry_count = 1
        delay = backoff.calculate_delay(state)
        assert delay == 1.0

        # Second retry: 2 seconds
        state.retry_count = 2
        delay = backoff.calculate_delay(state)
        assert delay == 2.0

        # Third retry: 4 seconds
        state.retry_count = 3
        delay = backoff.calculate_delay(state)
        assert delay == 4.0

    def test_max_delay_cap(self):
        """Test that delay is capped at max_delay."""
        config = RateLimitConfig(initial_delay=1.0, max_delay=5.0, jitter_factor=0)
        backoff = ExponentialBackoff(config)
        state = RateLimitState(current_tokens=100, last_refill=None)

        # Should be capped at 5 seconds
        state.retry_count = 10
        delay = backoff.calculate_delay(state)
        assert delay == 5.0

    def test_jitter_application(self):
        """Test jitter is applied correctly."""
        config = RateLimitConfig(initial_delay=10.0, jitter_factor=0.1)
        backoff = ExponentialBackoff(config)
        state = RateLimitState(current_tokens=100, last_refill=None)

        state.retry_count = 1
        delays = [backoff.calculate_delay(state) for _ in range(10)]

        # All delays should be within jitter range
        for delay in delays:
            assert 9.0 <= delay <= 11.0  # 10 ± 10%

        # Delays should vary (not all the same)
        assert len(set(delays)) > 1

    def test_reset_state(self):
        """Test state reset after success."""
        config = RateLimitConfig()
        backoff = ExponentialBackoff(config)
        state = RateLimitState(current_tokens=100, last_refill=None)

        state.retry_count = 3
        state.consecutive_failures = 3
        backoff.reset(state)

        assert state.retry_count == 0
        assert state.consecutive_failures == 0
        assert state.consecutive_successes == 1


class TestAdaptiveBackoff:
    """Test adaptive backoff implementation."""

    def test_adaptive_reduction_on_success(self):
        """Test delay reduction after consecutive successes."""
        config = RateLimitConfig(initial_delay=10.0, jitter_factor=0)
        backoff = AdaptiveBackoff(config)
        state = RateLimitState(current_tokens=100, last_refill=None)

        state.retry_count = 1
        state.consecutive_successes = 3  # Threshold for reduction

        delay = backoff.calculate_delay(state)
        assert delay < 10.0  # Should be reduced

    def test_adaptive_increase_on_failure(self):
        """Test delay increase after consecutive failures."""
        config = RateLimitConfig(initial_delay=10.0, jitter_factor=0)
        backoff = AdaptiveBackoff(config)
        state = RateLimitState(current_tokens=100, last_refill=None)

        state.retry_count = 1
        state.consecutive_failures = 2  # Threshold for increase

        delay = backoff.calculate_delay(state)
        assert delay > 10.0  # Should be increased


class TestTokenBucket:
    """Test token bucket implementation."""

    def test_initial_tokens(self):
        """Test initial token allocation."""
        config = RateLimitConfig(initial_tokens=100)
        bucket = TokenBucket(config)

        assert bucket.available() == 100

    def test_consume_tokens(self):
        """Test token consumption."""
        config = RateLimitConfig(initial_tokens=10)
        bucket = TokenBucket(config)

        # Consume 5 tokens
        assert bucket.consume(5) is True
        assert abs(bucket.available() - 5) < 0.001

        # Try to consume 10 tokens (should fail)
        assert bucket.consume(10) is False
        assert abs(bucket.available() - 5) < 0.001  # No change

        # Consume remaining tokens
        assert bucket.consume(5) is True
        assert bucket.available() < 0.001

    def test_token_refill(self):
        """Test token refill over time."""
        config = RateLimitConfig(initial_tokens=10, refill_rate=60)  # 1 per second
        bucket = TokenBucket(config)

        # Consume all tokens
        bucket.consume(10)
        assert bucket.available() < 0.001

        # Wait for refill
        time.sleep(2.1)
        assert bucket.available() >= 2  # Should have refilled at least 2 tokens

    def test_capacity_limit(self):
        """Test tokens don't exceed capacity."""
        config = RateLimitConfig(initial_tokens=10, refill_rate=600)  # 10 per second
        bucket = TokenBucket(config)

        # Wait for potential overfill
        time.sleep(2)
        assert bucket.available() == 10  # Should be capped at capacity

    def test_thread_safety(self):
        """Test thread-safe token operations."""
        config = RateLimitConfig(initial_tokens=1000)
        bucket = TokenBucket(config)

        consumed = []

        def consume_thread():
            for _ in range(100):
                if bucket.consume(1):
                    consumed.append(1)

        threads = [threading.Thread(target=consume_thread) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Exactly 1000 tokens should be consumed
        assert len(consumed) == 1000
        assert bucket.available() < 1  # Should be close to 0


class TestRateLimiter:
    """Test main RateLimiter class."""

    @pytest.mark.asyncio
    async def test_successful_execution(self):
        """Test successful function execution."""
        config = RateLimitConfig(initial_tokens=10)
        limiter = RateLimiter(config)

        async def test_func():
            return "success"

        result = await limiter.execute(test_func)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_sync_function_execution(self):
        """Test execution of synchronous function."""
        config = RateLimitConfig(initial_tokens=10)
        limiter = RateLimiter(config)

        def test_func():
            return "sync_success"

        result = await limiter.execute(test_func)
        assert result == "sync_success"

    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        """Test retry logic on failure."""
        config = RateLimitConfig(max_retries=3, initial_delay=0.1, jitter_factor=0)
        limiter = RateLimiter(config)

        call_count = 0

        async def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Rate limit exceeded")
            return "success"

        # Custom retry predicate
        def retry_on(e):
            return "rate limit" in str(e).lower()

        result = await limiter.execute(failing_func, retry_on=retry_on)
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_max_retries_exhausted(self):
        """Test exception when max retries exceeded."""
        config = RateLimitConfig(max_retries=2, initial_delay=0.1, jitter_factor=0)
        limiter = RateLimiter(config)

        async def always_fails():
            raise Exception("Rate limit exceeded")

        def retry_on(e):
            return True

        with pytest.raises(RateLimitExhausted) as exc_info:
            await limiter.execute(always_fails, retry_on=retry_on)

        assert exc_info.value.attempts == 2

    @pytest.mark.asyncio
    async def test_token_consumption(self):
        """Test token consumption during execution."""
        config = RateLimitConfig(initial_tokens=5)
        limiter = RateLimiter(config)

        async def test_func():
            return "success"

        # Execute 5 times (consuming 5 tokens)
        for _ in range(5):
            await limiter.execute(test_func, tokens=1)

        # 6th execution should wait or fail
        stats = limiter.get_stats()
        assert stats["token_bucket"]["tokens_available"] < 1

    @pytest.mark.asyncio
    async def test_progress_callback(self):
        """Test progress callback functionality."""
        config = RateLimitConfig(max_retries=3, initial_delay=0.1, jitter_factor=0)
        limiter = RateLimiter(config)

        progress_updates = []

        def progress_callback(update: ProgressUpdate):
            progress_updates.append(update)

        attempt_count = 0

        async def failing_func():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise Exception("Rate limit exceeded")
            return "success"

        def retry_on(e):
            return True

        await limiter.execute(failing_func, progress_callback=progress_callback, retry_on=retry_on)

        # Should have received progress updates
        assert len(progress_updates) > 0

    @pytest.mark.asyncio
    async def test_reset_functionality(self):
        """Test rate limiter reset."""
        config = RateLimitConfig(initial_tokens=10)
        limiter = RateLimiter(config)

        # Consume tokens and fail some attempts
        limiter.token_bucket.consume(9)
        limiter.state.retry_count = 3
        limiter.state.consecutive_failures = 2

        # Reset
        limiter.reset()

        # Check reset state
        assert limiter.token_bucket.available() == 10
        assert limiter.state.retry_count == 0
        assert limiter.state.consecutive_failures == 0

    def test_rate_limit_decorator_sync(self):
        """Test rate limit decorator on sync function."""

        @rate_limit(tokens=2.0)
        def test_func(value):
            return value * 2

        result = test_func(5)
        assert result == 10

    @pytest.mark.asyncio
    async def test_rate_limit_decorator_async(self):
        """Test rate limit decorator on async function."""

        @rate_limit(tokens=2.0)
        async def test_func(value):
            await asyncio.sleep(0.01)
            return value * 2

        result = await test_func(5)
        assert result == 10


class TestSlidingWindowCounter:
    """Test sliding window counter implementation."""

    def test_request_recording(self):
        """Test recording requests in window."""
        counter = SlidingWindowCounter(window_size=10.0, max_requests=5)

        # Record 3 requests
        assert counter.record(1) is True
        assert counter.record(1) is True
        assert counter.record(1) is True
        assert counter.available() == 2

        # Try to record 3 more (should fail)
        assert counter.record(3) is False
        assert counter.available() == 2

        # Record remaining 2
        assert counter.record(2) is True
        assert counter.available() == 0

    def test_window_expiration(self):
        """Test that old requests expire from window."""
        counter = SlidingWindowCounter(window_size=1.0, max_requests=5)

        # Fill the window
        counter.record(5)
        assert counter.available() == 0

        # Wait for window to expire
        time.sleep(1.1)
        assert counter.available() == 5


class TestIntegration:
    """Integration tests for complete rate limiting system."""

    @pytest.mark.asyncio
    async def test_full_retry_flow(self):
        """Test complete retry flow with backoff and tokens."""
        config = RateLimitConfig(
            initial_tokens=10,
            refill_rate=60,  # 1 per second
            max_retries=5,
            initial_delay=0.1,
            max_delay=1.0,
            jitter_factor=0.1,
        )
        limiter = RateLimiter(config, adaptive=True)

        call_times = []

        async def api_call():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise Exception("429 Too Many Requests")
            return {"data": "success"}

        def retry_on_429(e):
            return "429" in str(e)

        result = await limiter.execute(api_call, tokens=2, retry_on=retry_on_429)

        assert result == {"data": "success"}
        assert len(call_times) == 3

        # Check that delays were applied
        if len(call_times) >= 2:
            assert call_times[1] - call_times[0] >= 0.09  # At least initial delay minus jitter

    @pytest.mark.asyncio
    async def test_concurrent_rate_limiting(self):
        """Test rate limiting with concurrent requests."""
        config = RateLimitConfig(initial_tokens=10, refill_rate=0)  # No refill
        limiter = RateLimiter(config)

        results = []

        async def api_call(id):
            await asyncio.sleep(0.01)
            return f"result_{id}"

        # Create a closure function to capture the loop variable
        def create_api_call(call_id):
            return lambda: api_call(call_id)

        # Launch 15 concurrent requests (only 10 should succeed immediately)
        tasks = [limiter.execute(create_api_call(i), tokens=1) for i in range(15)]

        # Some should succeed, some should wait/fail
        completed = 0
        for task in asyncio.as_completed(tasks):
            try:
                result = await asyncio.wait_for(task, timeout=0.5)
                results.append(result)
                completed += 1
            except (asyncio.TimeoutError, TokenBudgetExceeded):
                pass

        # Should have completed about 10 (initial tokens)
        assert 8 <= completed <= 12  # Allow some variance due to timing


class TestPerformance:
    """Performance and stress tests."""

    @pytest.mark.asyncio
    async def test_high_throughput(self):
        """Test performance under high load."""
        config = RateLimitConfig(
            initial_tokens=1000,
            refill_rate=600,  # 10 per second
            max_retries=2,
            initial_delay=0.01,
        )
        limiter = RateLimiter(config)

        start_time = time.time()
        success_count = 0

        async def quick_task():
            return True

        # Execute many requests
        for _ in range(100):
            try:
                result = await limiter.execute(quick_task, tokens=1)
                if result:
                    success_count += 1
            except (RateLimitExhausted, TokenBudgetExceeded):
                pass

        elapsed = time.time() - start_time

        # Should handle 100 requests reasonably quickly
        assert elapsed < 5.0
        assert success_count > 50  # Most should succeed
