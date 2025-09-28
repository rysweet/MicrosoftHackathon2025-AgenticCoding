"""Exponential backoff implementation with jitter."""

import random
import time
from typing import Callable, Optional

from .models import RateLimitConfig, RateLimitState


class ExponentialBackoff:
    """Exponential backoff calculator with jitter.

    Implements exponential backoff with configurable parameters and
    random jitter to prevent thundering herd problems.
    """

    def __init__(self, config: RateLimitConfig):
        """Initialize backoff calculator.

        Args:
            config: Rate limiting configuration
        """
        self.config = config
        self._random = random.Random()

    def calculate_delay(self, state: RateLimitState) -> float:
        """Calculate next backoff delay with jitter.

        Args:
            state: Current rate limit state

        Returns:
            Delay in seconds with jitter applied
        """
        if state.retry_count == 0:
            return 0.0

        # Calculate base delay using exponential backoff
        base_delay = self.config.initial_delay * (
            self.config.backoff_multiplier ** (state.retry_count - 1)
        )

        # Cap at maximum delay
        base_delay = min(base_delay, self.config.max_delay)

        # Apply jitter
        delay_with_jitter = self._apply_jitter(base_delay)

        # Store for next calculation
        state.last_delay = delay_with_jitter

        return delay_with_jitter

    def _apply_jitter(self, delay: float) -> float:
        """Apply random jitter to delay.

        Args:
            delay: Base delay in seconds

        Returns:
            Delay with jitter applied
        """
        if self.config.jitter_factor == 0:
            return delay

        # Calculate jitter range
        jitter_range = delay * self.config.jitter_factor

        # Apply random jitter (positive or negative)
        jitter = self._random.uniform(-jitter_range, jitter_range)

        # Ensure delay remains positive
        return max(0.1, delay + jitter)  # Minimum 0.1s delay

    def reset(self, state: RateLimitState):
        """Reset backoff state after success.

        Args:
            state: Rate limit state to reset
        """
        state.reset_backoff()

    def should_retry(self, state: RateLimitState) -> bool:
        """Check if retry should be attempted.

        Args:
            state: Current rate limit state

        Returns:
            True if retry should proceed
        """
        return state.retry_count < self.config.max_retries

    def estimate_total_wait(self, attempts_remaining: int) -> float:
        """Estimate total wait time for remaining attempts.

        Args:
            attempts_remaining: Number of attempts left

        Returns:
            Estimated total wait time in seconds
        """
        if attempts_remaining <= 0:
            return 0.0

        total = 0.0
        for i in range(attempts_remaining):
            delay = self.config.initial_delay * (self.config.backoff_multiplier**i)
            delay = min(delay, self.config.max_delay)
            total += delay

        return total

    def get_stats(self, state: RateLimitState) -> dict:
        """Get backoff statistics.

        Args:
            state: Current rate limit state

        Returns:
            Dictionary of backoff statistics
        """
        return {
            "retry_count": state.retry_count,
            "last_delay": state.last_delay,
            "next_delay": self.calculate_delay(state) if self.should_retry(state) else 0,
            "max_retries": self.config.max_retries,
            "consecutive_failures": state.consecutive_failures,
            "consecutive_successes": state.consecutive_successes,
            "total_retries": state.total_retries,
        }


class AdaptiveBackoff(ExponentialBackoff):
    """Adaptive backoff that adjusts based on success/failure patterns.

    Extends basic exponential backoff with adaptive behavior that
    reduces delays after consecutive successes and increases them
    after consecutive failures.
    """

    def __init__(self, config: RateLimitConfig):
        """Initialize adaptive backoff.

        Args:
            config: Rate limiting configuration
        """
        super().__init__(config)
        self.success_threshold = 3  # Successes before reducing delay
        self.failure_threshold = 2  # Failures before increasing delay
        self.adaptation_factor = 0.5  # How much to adapt delays

    def calculate_delay(self, state: RateLimitState) -> float:
        """Calculate adaptive backoff delay.

        Args:
            state: Current rate limit state

        Returns:
            Adapted delay in seconds
        """
        base_delay = super().calculate_delay(state)

        if base_delay == 0:
            return 0

        # Adapt based on success/failure patterns
        if state.consecutive_successes >= self.success_threshold:
            # Reduce delay after consecutive successes
            factor = 1.0 - (self.adaptation_factor * min(state.consecutive_successes / 10, 1.0))
            base_delay *= factor

        elif state.consecutive_failures >= self.failure_threshold:
            # Increase delay after consecutive failures
            factor = 1.0 + (self.adaptation_factor * min(state.consecutive_failures / 5, 1.0))
            base_delay *= factor

        return min(base_delay, self.config.max_delay)


def wait_with_progress(delay: float, callback: Optional[Callable] = None) -> bool:
    """Wait with optional progress updates.

    Args:
        delay: Time to wait in seconds
        callback: Optional callback for progress updates

    Returns:
        True if wait completed, False if interrupted
    """
    if delay <= 0:
        return True

    start_time = time.time()
    update_interval = min(1.0, delay / 10)  # Update every second or 10% of delay

    while True:
        elapsed = time.time() - start_time
        remaining = delay - elapsed

        if remaining <= 0:
            break

        if callback:
            progress = min(elapsed / delay, 1.0)
            callback(progress, remaining)

        # Sleep for update interval or remaining time
        sleep_time = min(update_interval, remaining)
        time.sleep(sleep_time)

    return True
