"""Core rate limiting implementation."""

import asyncio
import functools
import inspect
import logging
import threading
import time
from datetime import datetime
from typing import Awaitable, Callable, Optional, TypeVar, Union, cast

from .backoff import AdaptiveBackoff, ExponentialBackoff
from .models import (
    ProgressCallback,
    ProgressUpdate,
    RateLimitConfig,
    RateLimitExhausted,
    RateLimitState,
    RateLimitStatus,
    RetryPredicate,
    RetryResult,
    TokenBudgetExceeded,
)
from .token_budget import TokenBucket

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RateLimiter:
    """Main rate limiting orchestrator.

    Combines token bucket and exponential backoff strategies to provide
    comprehensive rate limiting protection with automatic retry.
    """

    def __init__(self, config: Optional[RateLimitConfig] = None, adaptive: bool = False):
        """Initialize rate limiter.

        Args:
            config: Rate limiting configuration (uses defaults if None)
            adaptive: Use adaptive backoff instead of fixed exponential
        """
        self.config = config or RateLimitConfig()
        self.token_bucket = TokenBucket(self.config)
        self.backoff = AdaptiveBackoff(self.config) if adaptive else ExponentialBackoff(self.config)
        self.state = RateLimitState(
            current_tokens=self.config.initial_tokens, last_refill=datetime.now()
        )
        self._lock = threading.RLock()

    async def execute(
        self,
        func: Callable[[], Union[T, Awaitable[T]]],
        tokens: float = 1.0,
        progress_callback: Optional[ProgressCallback] = None,
        retry_on: Optional[RetryPredicate] = None,
    ) -> T:
        """Execute function with rate limiting protection.

        Args:
            func: Function to execute (sync or async)
            tokens: Number of tokens required for this operation
            progress_callback: Optional callback for progress updates
            retry_on: Optional predicate to determine if retry is needed

        Returns:
            Result of function execution

        Raises:
            RateLimitExhausted: If max retries exceeded
            TokenBudgetExceeded: If tokens cannot be obtained
        """
        # Determine if function is async using inspect to avoid test execution
        is_async = inspect.iscoroutinefunction(func)

        result = await self._execute_with_retry(func, tokens, progress_callback, retry_on, is_async)

        if result.status == RateLimitStatus.SUCCESS:
            return cast(T, result.value)
        elif result.status == RateLimitStatus.EXHAUSTED:
            raise RateLimitExhausted(result.attempts, result.total_delay, result.error)
        else:
            raise result.error or Exception(f"Unexpected status: {result.status}")

    async def _execute_with_retry(
        self,
        func: Callable,
        tokens: float,
        progress_callback: Optional[ProgressCallback],
        retry_on: Optional[RetryPredicate],
        is_async: bool,
    ) -> RetryResult:
        """Execute with retry logic.

        Args:
            func: Function to execute
            tokens: Required tokens
            progress_callback: Progress callback
            retry_on: Retry predicate
            is_async: Whether function is async

        Returns:
            RetryResult with execution outcome
        """
        total_delay = 0.0
        last_error = None

        while self.backoff.should_retry(self.state):
            with self._lock:
                self.state.record_request()

                # Check token availability
                if not self.token_bucket.consume(tokens):
                    # Wait for tokens
                    success = await self._wait_for_tokens_async(tokens, progress_callback)
                    if not success:
                        return RetryResult(
                            status=RateLimitStatus.EXHAUSTED,
                            error=TokenBudgetExceeded(tokens, self.token_bucket.available()),
                            attempts=self.state.retry_count,
                            total_delay=total_delay,
                            tokens_consumed=0,
                        )

                # Calculate delay if this is a retry
                delay = self.backoff.calculate_delay(self.state)
                if delay > 0:
                    if progress_callback:
                        self._send_progress(
                            progress_callback,
                            self.state.retry_count,
                            delay,
                            self.token_bucket.available(),
                        )

                    # Wait with progress updates
                    await self._wait_async(delay, progress_callback)
                    total_delay += delay

            try:
                # Execute function
                if is_async:
                    result = await func()
                else:
                    result = await asyncio.get_event_loop().run_in_executor(None, func)

                # Success - reset backoff
                with self._lock:
                    self.backoff.reset(self.state)

                return RetryResult(
                    status=RateLimitStatus.SUCCESS,
                    value=result,
                    attempts=self.state.retry_count + 1,
                    total_delay=total_delay,
                    tokens_consumed=tokens,
                )

            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {self.state.retry_count + 1} failed: {e}")

                # Check if we should retry this error
                should_retry = self._should_retry_error(e, retry_on)
                if not should_retry:
                    return RetryResult(
                        status=RateLimitStatus.ERROR,
                        error=e,
                        attempts=self.state.retry_count + 1,
                        total_delay=total_delay,
                        tokens_consumed=tokens,
                    )

                # Increment retry count
                with self._lock:
                    self.state.increment_retry()

        # Max retries exhausted
        return RetryResult(
            status=RateLimitStatus.EXHAUSTED,
            error=last_error,
            attempts=self.state.retry_count,
            total_delay=total_delay,
            tokens_consumed=0,
        )

    def _should_retry_error(self, error: Exception, retry_on: Optional[RetryPredicate]) -> bool:
        """Determine if error should trigger retry.

        Args:
            error: Exception that occurred
            retry_on: Optional custom predicate

        Returns:
            True if retry should be attempted
        """
        if retry_on:
            return retry_on(error)

        # Default retry logic - retry on common rate limit errors
        error_msg = str(error).lower()
        rate_limit_indicators = [
            "rate limit",
            "too many requests",
            "429",
            "throttled",
            "quota exceeded",
            "retry",
        ]

        return any(indicator in error_msg for indicator in rate_limit_indicators)

    async def _wait_for_tokens_async(
        self, tokens: float, progress_callback: Optional[ProgressCallback]
    ) -> bool:
        """Wait for tokens to become available (async).

        Args:
            tokens: Number of tokens needed
            progress_callback: Progress callback

        Returns:
            True if tokens obtained, False if timeout
        """
        start_time = time.time()
        timeout = self.config.max_delay

        while time.time() - start_time < timeout:
            if self.token_bucket.consume(tokens):
                return True

            wait_time = min(0.1, timeout - (time.time() - start_time))
            if wait_time <= 0:
                break

            if progress_callback:
                elapsed = time.time() - start_time
                self._send_progress(
                    progress_callback,
                    self.state.retry_count,
                    timeout - elapsed,
                    self.token_bucket.available(),
                    message="Waiting for tokens",
                )

            await asyncio.sleep(wait_time)

        return False

    async def _wait_async(self, delay: float, progress_callback: Optional[ProgressCallback]):
        """Async wait with progress updates.

        Args:
            delay: Time to wait in seconds
            progress_callback: Progress callback
        """
        if delay <= 0:
            return

        start_time = time.time()
        update_interval = min(1.0, delay / 10)

        while True:
            elapsed = time.time() - start_time
            remaining = delay - elapsed

            if remaining <= 0:
                break

            if progress_callback:
                progress = min(elapsed / delay, 1.0)
                self._send_progress(
                    progress_callback,
                    self.state.retry_count,
                    remaining,
                    self.token_bucket.available(),
                    message=f"Backoff {int(progress * 100)}%",
                )

            sleep_time = min(update_interval, remaining)
            await asyncio.sleep(sleep_time)

    def _send_progress(
        self,
        callback: ProgressCallback,
        attempt: int,
        delay: float,
        tokens: float,
        message: Optional[str] = None,
    ):
        """Send progress update.

        Args:
            callback: Progress callback function
            attempt: Current attempt number
            delay: Current or remaining delay
            tokens: Available tokens
            message: Optional status message
        """
        update = ProgressUpdate(
            attempt=attempt,
            max_attempts=self.config.max_retries,
            delay=delay,
            tokens_remaining=tokens,
            estimated_wait=self.backoff.estimate_total_wait(self.config.max_retries - attempt),
            message=message,
        )
        try:
            callback(update)
        except Exception as e:
            logger.warning(f"Progress callback error: {e}")

    def reset(self):
        """Reset rate limiter to initial state."""
        with self._lock:
            self.token_bucket.reset()
            self.state = RateLimitState(
                current_tokens=self.config.initial_tokens, last_refill=datetime.now()
            )

    def get_stats(self) -> dict:
        """Get rate limiter statistics.

        Returns:
            Dictionary of statistics
        """
        with self._lock:
            return {
                "state": {
                    "retry_count": self.state.retry_count,
                    "total_requests": self.state.total_requests,
                    "total_retries": self.state.total_retries,
                    "consecutive_successes": self.state.consecutive_successes,
                    "consecutive_failures": self.state.consecutive_failures,
                },
                "token_bucket": self.token_bucket.get_stats(),
                "backoff": self.backoff.get_stats(self.state),
            }


def rate_limit(
    tokens: float = 1.0,
    config: Optional[RateLimitConfig] = None,
    adaptive: bool = False,
) -> Callable:
    """Decorator for rate-limited functions.

    Args:
        tokens: Tokens required per call
        config: Rate limit configuration
        adaptive: Use adaptive backoff

    Returns:
        Decorated function with rate limiting

    Example:
        @rate_limit(tokens=2.0)
        async def api_call():
            return await fetch_data()
    """
    limiter = RateLimiter(config, adaptive)

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await limiter.execute(
                lambda: func(*args, **kwargs),
                tokens=tokens,
            )

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                # Check if we're in an async context
                asyncio.get_running_loop()
                # If we get here, there's a running loop - we can't use run_until_complete
                raise RuntimeError(
                    "Cannot call sync rate-limited function from async context. "
                    "Use the async version of the function or call from sync context."
                )
            except RuntimeError as e:
                if (
                    "no running event loop" in str(e).lower()
                    or "no current event loop" in str(e).lower()
                ):
                    # No running loop, create a new one
                    loop = asyncio.new_event_loop()
                    try:
                        return loop.run_until_complete(
                            limiter.execute(
                                lambda: func(*args, **kwargs),
                                tokens=tokens,
                            )
                        )
                    finally:
                        loop.close()
                else:
                    # Re-raise the error if it's not about missing event loop
                    raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
