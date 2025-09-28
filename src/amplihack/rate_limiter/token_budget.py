"""Token bucket implementation for rate limiting."""

import threading
import time
from typing import Optional, Tuple

from .models import RateLimitConfig


class TokenBucket:
    """Thread-safe token bucket implementation.

    Implements the token bucket algorithm for rate limiting with
    automatic refill based on elapsed time.
    """

    def __init__(self, config: RateLimitConfig):
        """Initialize token bucket.

        Args:
            config: Rate limiting configuration
        """
        self.config = config
        self.capacity = config.initial_tokens
        self.tokens = float(config.initial_tokens)
        self.refill_rate = config.refill_rate / 60.0  # Convert to per-second
        self.last_refill = time.time()
        self._lock = threading.RLock()

    def _refill(self) -> float:
        """Refill tokens based on elapsed time.

        Returns:
            Number of tokens added
        """
        now = time.time()
        elapsed = now - self.last_refill

        if elapsed <= 0:
            return 0

        # Calculate tokens to add
        tokens_to_add = elapsed * self.refill_rate

        # Add tokens up to capacity
        old_tokens = self.tokens
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now

        return self.tokens - old_tokens

    def consume(self, tokens: float = 1.0) -> bool:
        """Attempt to consume tokens.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens were consumed, False otherwise
        """
        with self._lock:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def try_consume(self, tokens: float = 1.0) -> Tuple[bool, float]:
        """Try to consume tokens and return wait time if not available.

        Args:
            tokens: Number of tokens to consume

        Returns:
            Tuple of (success, wait_time_if_failed)
        """
        with self._lock:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True, 0.0

            # Calculate wait time for tokens to be available
            deficit = tokens - self.tokens
            wait_time = deficit / self.refill_rate if self.refill_rate > 0 else float("inf")

            # Check if wait time is reasonable
            if wait_time > self.config.max_delay:
                return False, self.config.max_delay

            return False, wait_time

    def wait_for_tokens(self, tokens: float = 1.0, timeout: Optional[float] = None) -> bool:
        """Wait for tokens to become available.

        Args:
            tokens: Number of tokens needed
            timeout: Maximum time to wait in seconds

        Returns:
            True if tokens were consumed, False if timeout
        """
        start_time = time.time()
        timeout = timeout or self.config.max_delay

        while True:
            success, wait_time = self.try_consume(tokens)
            if success:
                return True

            elapsed = time.time() - start_time
            if elapsed >= timeout:
                return False

            # Wait for tokens to refill
            sleep_time = min(wait_time, timeout - elapsed, 0.1)  # Check every 100ms
            if sleep_time <= 0:
                return False

            time.sleep(sleep_time)

    def available(self) -> float:
        """Get current available tokens.

        Returns:
            Number of available tokens
        """
        with self._lock:
            self._refill()
            return self.tokens

    def reset(self):
        """Reset bucket to initial state."""
        with self._lock:
            self.tokens = float(self.capacity)
            self.last_refill = time.time()

    def set_capacity(self, capacity: int):
        """Update bucket capacity.

        Args:
            capacity: New capacity
        """
        with self._lock:
            self.capacity = capacity
            if self.tokens > capacity:
                self.tokens = float(capacity)

    def set_refill_rate(self, rate: float):
        """Update refill rate.

        Args:
            rate: New refill rate (tokens per minute)
        """
        with self._lock:
            self.refill_rate = rate / 60.0

    def get_stats(self) -> dict:
        """Get bucket statistics.

        Returns:
            Dictionary of bucket statistics
        """
        with self._lock:
            self._refill()
            return {
                "tokens_available": self.tokens,
                "capacity": self.capacity,
                "refill_rate_per_min": self.refill_rate * 60,
                "utilization": 1.0 - (self.tokens / self.capacity) if self.capacity > 0 else 0,
            }


class LeakyBucket(TokenBucket):
    """Leaky bucket variant with continuous drain.

    Extends token bucket with a continuous drain rate, useful for
    sustained rate limiting rather than burst control.
    """

    def __init__(self, config: RateLimitConfig):
        """Initialize leaky bucket.

        Args:
            config: Rate limiting configuration
        """
        super().__init__(config)
        self.drain_rate = config.refill_rate / 60.0  # Use refill rate as drain rate
        self.last_drain = time.time()

    def _drain(self) -> float:
        """Drain tokens based on elapsed time.

        Returns:
            Number of tokens drained
        """
        now = time.time()
        elapsed = now - self.last_drain

        if elapsed <= 0:
            return 0

        # Calculate tokens to drain
        tokens_to_drain = elapsed * self.drain_rate

        # Drain tokens
        old_tokens = self.tokens
        self.tokens = max(0, self.tokens - tokens_to_drain)
        self.last_drain = now

        return old_tokens - self.tokens

    def _refill(self) -> float:
        """Refill and drain tokens.

        Returns:
            Net change in tokens
        """
        refilled = super()._refill()
        drained = self._drain()
        return refilled - drained


class SlidingWindowCounter:
    """Sliding window counter for rate limiting.

    Tracks request counts in a sliding time window for more accurate
    rate limiting compared to fixed windows.
    """

    def __init__(self, window_size: float = 60.0, max_requests: int = 100):
        """Initialize sliding window counter.

        Args:
            window_size: Window size in seconds
            max_requests: Maximum requests allowed in window
        """
        self.window_size = window_size
        self.max_requests = max_requests
        self.requests = []  # List of (timestamp, count) tuples
        self._lock = threading.RLock()

    def _cleanup(self):
        """Remove expired entries from window."""
        cutoff = time.time() - self.window_size
        self.requests = [(ts, count) for ts, count in self.requests if ts > cutoff]

    def record(self, count: int = 1) -> bool:
        """Record request(s) if allowed.

        Args:
            count: Number of requests to record

        Returns:
            True if request was allowed, False if rate limit exceeded
        """
        with self._lock:
            self._cleanup()

            # Calculate current total
            current_total = sum(c for _, c in self.requests)

            if current_total + count > self.max_requests:
                return False

            # Add request
            self.requests.append((time.time(), count))
            return True

    def available(self) -> int:
        """Get available request capacity.

        Returns:
            Number of available requests
        """
        with self._lock:
            self._cleanup()
            current_total = sum(c for _, c in self.requests)
            return max(0, self.max_requests - current_total)

    def reset(self):
        """Reset counter."""
        with self._lock:
            self.requests.clear()

    def get_stats(self) -> dict:
        """Get counter statistics.

        Returns:
            Dictionary of counter statistics
        """
        with self._lock:
            self._cleanup()
            current_total = sum(c for _, c in self.requests)
            return {
                "current_count": current_total,
                "max_requests": self.max_requests,
                "window_size": self.window_size,
                "utilization": current_total / self.max_requests if self.max_requests > 0 else 0,
                "available": self.available(),
            }
