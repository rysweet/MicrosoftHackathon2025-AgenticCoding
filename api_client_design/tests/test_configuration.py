#!/usr/bin/env python3
"""
Unit tests for configuration classes (RetryConfig, RateLimiter)

Testing pyramid: 60% unit tests
Focus on configuration logic and behavior
"""

import pytest
import time
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api_client import RetryConfig, SimpleRateLimiter


class TestRetryConfig:
    """Test RetryConfig behavior"""

    def test_default_configuration(self):
        """RetryConfig has sensible defaults"""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.backoff_factor == 1.0
        assert config.retry_on_status == (429, 500, 502, 503, 504)

    def test_custom_configuration(self):
        """RetryConfig accepts custom values"""
        config = RetryConfig(
            max_retries=5,
            backoff_factor=2.0,
            retry_on_status=(429, 503)
        )
        assert config.max_retries == 5
        assert config.backoff_factor == 2.0
        assert config.retry_on_status == (429, 503)

    def test_should_retry_logic(self):
        """should_retry correctly determines retry eligibility"""
        config = RetryConfig(
            max_retries=3,
            retry_on_status=(429, 503)
        )

        # Should retry on configured status codes
        assert config.should_retry(429, attempt=0) is True
        assert config.should_retry(503, attempt=0) is True

        # Should not retry on non-configured status
        assert config.should_retry(404, attempt=0) is False
        assert config.should_retry(500, attempt=0) is False

        # Should not retry after max attempts
        assert config.should_retry(429, attempt=3) is False
        assert config.should_retry(429, attempt=4) is False

    def test_exponential_backoff_calculation(self):
        """get_backoff_time calculates exponential backoff"""
        config = RetryConfig(backoff_factor=1.0)

        # Exponential: factor * (2 ^ attempt)
        assert config.get_backoff_time(0) == 1.0  # 1 * 2^0 = 1
        assert config.get_backoff_time(1) == 2.0  # 1 * 2^1 = 2
        assert config.get_backoff_time(2) == 4.0  # 1 * 2^2 = 4
        assert config.get_backoff_time(3) == 8.0  # 1 * 2^3 = 8

    def test_backoff_with_custom_factor(self):
        """Backoff factor scales wait times"""
        config = RetryConfig(backoff_factor=0.5)

        assert config.get_backoff_time(0) == 0.5  # 0.5 * 2^0
        assert config.get_backoff_time(1) == 1.0  # 0.5 * 2^1
        assert config.get_backoff_time(2) == 2.0  # 0.5 * 2^2

        config2 = RetryConfig(backoff_factor=3.0)
        assert config2.get_backoff_time(0) == 3.0  # 3 * 2^0
        assert config2.get_backoff_time(1) == 6.0  # 3 * 2^1


class TestSimpleRateLimiter:
    """Test SimpleRateLimiter token bucket implementation"""

    def test_initialization(self):
        """RateLimiter initializes with correct parameters"""
        limiter = SimpleRateLimiter(
            requests_per_second=10.0,
            burst_size=5
        )
        assert limiter.requests_per_second == 10.0
        assert limiter.burst_size == 5
        assert limiter._tokens == 5.0  # Start with full burst

    def test_acquire_with_available_tokens(self):
        """acquire() proceeds immediately with available tokens"""
        limiter = SimpleRateLimiter(
            requests_per_second=10.0,
            burst_size=5
        )

        # Should not block with available tokens
        start = time.time()
        limiter.acquire()
        elapsed = time.time() - start

        assert elapsed < 0.01  # Should be nearly instant
        assert limiter._tokens == 4.0  # One token consumed

    def test_acquire_burst_capacity(self):
        """Burst capacity allows rapid requests"""
        limiter = SimpleRateLimiter(
            requests_per_second=1.0,  # Slow rate
            burst_size=3  # But can burst 3
        )

        # Should handle burst without blocking
        start = time.time()
        for _ in range(3):
            limiter.acquire()
        elapsed = time.time() - start

        assert elapsed < 0.1  # All three should be fast
        assert limiter._tokens < 1  # Tokens depleted

    def test_acquire_rate_limiting(self):
        """acquire() blocks when tokens exhausted"""
        limiter = SimpleRateLimiter(
            requests_per_second=10.0,
            burst_size=1
        )

        # First request uses the burst token
        limiter.acquire()
        assert limiter._tokens == 0

        # Second request should wait
        start = time.time()
        limiter.acquire()
        elapsed = time.time() - start

        # Should wait approximately 0.1 seconds (1/10 rps)
        assert 0.05 < elapsed < 0.15

    def test_token_replenishment(self):
        """Tokens replenish over time"""
        limiter = SimpleRateLimiter(
            requests_per_second=10.0,
            burst_size=5
        )

        # Use all tokens
        for _ in range(5):
            limiter.acquire()

        assert limiter._tokens < 1

        # Wait for replenishment
        time.sleep(0.3)  # Should replenish ~3 tokens

        # Check tokens were replenished (approximately)
        limiter.acquire()  # This updates token count
        assert 1 < limiter._tokens < 4  # Some tokens replenished

    def test_reset_functionality(self):
        """reset() restores full burst capacity"""
        limiter = SimpleRateLimiter(
            requests_per_second=5.0,
            burst_size=3
        )

        # Use some tokens
        limiter.acquire()
        limiter.acquire()
        assert limiter._tokens < 2

        # Reset
        limiter.reset()
        assert limiter._tokens == 3.0
        assert limiter._last_request == 0.0

    def test_maximum_burst_enforcement(self):
        """Tokens never exceed burst_size"""
        limiter = SimpleRateLimiter(
            requests_per_second=100.0,  # Very fast rate
            burst_size=5
        )

        # Wait a long time (would accumulate many tokens)
        limiter._last_request = time.time() - 10  # 10 seconds ago
        limiter._tokens = 5.0

        # Acquire should cap at burst_size
        limiter.acquire()
        # After replenishment and usage, should be at most burst_size - 1
        assert limiter._tokens <= 4.0


class TestRateLimiterProtocol:
    """Test that SimpleRateLimiter follows the RateLimiter protocol"""

    def test_protocol_methods_exist(self):
        """SimpleRateLimiter implements required protocol methods"""
        limiter = SimpleRateLimiter(requests_per_second=1.0)

        # Protocol requires these methods
        assert hasattr(limiter, 'acquire')
        assert hasattr(limiter, 'reset')
        assert callable(limiter.acquire)
        assert callable(limiter.reset)

    def test_custom_rate_limiter_implementation(self):
        """Custom rate limiter can implement the protocol"""

        class CustomRateLimiter:
            """Minimal custom implementation"""

            def __init__(self):
                self.count = 0

            def acquire(self) -> None:
                self.count += 1
                if self.count > 3:
                    time.sleep(0.01)  # Simple rate limit

            def reset(self) -> None:
                self.count = 0

        # Should be usable as a RateLimiter
        limiter = CustomRateLimiter()
        limiter.acquire()
        limiter.reset()
        assert limiter.count == 0


class TestConfigurationIntegration:
    """Test configuration components work together"""

    def test_retry_and_rate_limit_independence(self):
        """RetryConfig and RateLimiter are independent"""
        retry = RetryConfig(max_retries=5)
        limiter = SimpleRateLimiter(requests_per_second=10.0)

        # They don't interact directly
        assert retry.should_retry(503, 0) is True
        limiter.acquire()  # Works independently

    def test_configuration_combinations(self):
        """Different configuration combinations are valid"""
        configs = [
            # Aggressive retry, slow rate limit
            (RetryConfig(max_retries=10), SimpleRateLimiter(1.0)),
            # No retry, fast rate limit
            (RetryConfig(max_retries=0), SimpleRateLimiter(100.0)),
            # Balanced
            (RetryConfig(max_retries=3), SimpleRateLimiter(10.0)),
        ]

        for retry_config, rate_limiter in configs:
            # All combinations should be valid
            assert retry_config.max_retries >= 0
            assert rate_limiter.requests_per_second > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])