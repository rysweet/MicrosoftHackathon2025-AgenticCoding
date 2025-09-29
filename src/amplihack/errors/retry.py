"""Retry decorator with exponential backoff."""

import functools
import random
import time
from typing import Any, Callable, Optional, Tuple, Type

from .base import TimeoutError
from .logging import error_logger, log_error


class RetryBudget:
    """Budget manager for retry operations based on total delay time."""

    def __init__(self, max_total_delay: float = 100.0):
        """Initialize retry budget.

        Args:
            max_total_delay: Maximum total delay time in seconds
        """
        self.max_total_delay = max_total_delay
        self.used_delay = 0.0

    def can_retry(self, delay: float) -> bool:
        """Check if retry is allowed with given delay.

        Args:
            delay: Proposed delay for next retry

        Returns:
            True if retry with given delay is within budget
        """
        return self.used_delay + delay <= self.max_total_delay

    def consume_delay(self, delay: float) -> None:
        """Consume delay from budget.

        Args:
            delay: Delay time to consume
        """
        self.used_delay += delay

    def remaining_budget(self) -> float:
        """Get remaining budget.

        Returns:
            Remaining delay budget in seconds
        """
        return max(0.0, self.max_total_delay - self.used_delay)


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        budget: Optional[RetryBudget] = None,
        retryable_errors: Optional[Tuple[Type[Exception], ...]] = None,
        non_retryable_errors: Optional[Tuple[Type[Exception], ...]] = None,
    ):
        """Initialize retry configuration.

        Args:
            max_attempts: Maximum number of retry attempts
            base_delay: Base delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            exponential_base: Base for exponential backoff calculation
            jitter: Whether to add random jitter to delays
            budget: Optional retry budget for delay time tracking
            retryable_errors: Tuple of exception types that should trigger retries
            non_retryable_errors: Tuple of exception types that should not trigger retries

        Raises:
            ValueError: If configuration parameters are invalid
        """
        # Validate max_attempts
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if max_attempts > 5:
            raise ValueError("max_attempts cannot exceed 5")

        # Validate delays
        if base_delay <= 0:
            raise ValueError("base_delay must be positive")
        if max_delay < base_delay:
            raise ValueError("max_delay must be >= base_delay")
        if max_delay > 30.0:
            raise ValueError("max_delay cannot exceed 30 seconds")

        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.budget = budget or RetryBudget()

        # Import error classes from base module
        from .base import ProcessError, SecurityError, ValidationError

        # Default retryable errors (network, temporary failures, process errors)
        if retryable_errors is None:
            self.retryable_errors = (
                ConnectionError,
                TimeoutError,
                OSError,
                ProcessError,
            )
        else:
            self.retryable_errors = retryable_errors

        # Default non-retryable errors (validation, security, permanent failures)
        if non_retryable_errors is None:
            self.non_retryable_errors = (
                ValidationError,
                SecurityError,
                ValueError,
                TypeError,
                KeyboardInterrupt,
                SystemExit,
            )
        else:
            self.non_retryable_errors = non_retryable_errors

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt.

        Args:
            attempt: Attempt number (1-based)

        Returns:
            Delay in seconds
        """
        if attempt <= 0:
            return 0.0

        # Exponential backoff: base_delay * (exponential_base ^ (attempt - 1))
        delay = self.base_delay * (self.exponential_base ** (attempt - 1))
        delay = min(delay, self.max_delay)

        # Add jitter (±25% of delay) if enabled
        if self.jitter:
            jitter_amount = delay * 0.25
            delay += random.uniform(-jitter_amount, jitter_amount)

        return max(0.0, delay)

    def should_retry(self, error: Exception, attempt: int) -> bool:
        """Determine if an error should trigger a retry.

        Args:
            error: Exception that occurred
            attempt: Current attempt number (1-based)

        Returns:
            True if should retry, False otherwise
        """
        if attempt >= self.max_attempts:
            return False

        if isinstance(error, self.non_retryable_errors):
            return False

        return isinstance(error, self.retryable_errors)


def retry_on_error(
    config: Optional[RetryConfig] = None,
    **config_kwargs,
) -> Callable:
    """Decorator for adding retry logic with exponential backoff.

    Args:
        config: RetryConfig instance, or None to use defaults
        **config_kwargs: Keyword arguments to create RetryConfig if config is None

    Returns:
        Decorator function
    """
    if config is None:
        config = RetryConfig(**config_kwargs)

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_error = None
            attempt = 0

            for attempt in range(1, config.max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as error:
                    last_error = error

                    # Log the error
                    log_error(
                        error,
                        context={
                            "function": func.__name__,
                            "attempt": attempt,
                            "max_attempts": config.max_attempts,
                        },
                    )

                    # Check if we should retry
                    if not config.should_retry(error, attempt):
                        break

                    # Calculate delay for next attempt
                    if attempt < config.max_attempts:
                        delay = config.calculate_delay(attempt)

                        # Check budget before sleeping
                        if not config.budget.can_retry(delay):
                            break

                        # Log retry attempt
                        error_logger.log_retry_attempt(
                            error,
                            attempt,
                            config.max_attempts,
                            delay,
                            context={"function": func.__name__},
                        )

                        # Consume delay from budget and sleep
                        config.budget.consume_delay(delay)
                        time.sleep(delay)

            # Re-raise the last error
            if last_error:
                # Log retry exhaustion if we tried multiple times
                if attempt > 1:
                    error_logger.log_retry_exhausted(
                        last_error, attempt, context={"function": func.__name__}
                    )
                raise last_error

        return wrapper

    return decorator


def retry_async(
    config: Optional[RetryConfig] = None,
    **config_kwargs,
) -> Callable:
    """Async version of retry decorator.

    Args:
        config: RetryConfig instance, or None to use defaults
        **config_kwargs: Keyword arguments to create RetryConfig if config is None

    Returns:
        Async decorator function
    """
    import asyncio

    if config is None:
        config = RetryConfig(**config_kwargs)

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_error = None
            attempt = 0

            for attempt in range(1, config.max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as error:
                    last_error = error

                    # Log the error
                    log_error(
                        error,
                        context={
                            "function": func.__name__,
                            "attempt": attempt,
                            "max_attempts": config.max_attempts,
                        },
                    )

                    # Check if we should retry
                    if not config.should_retry(error, attempt):
                        break

                    # Calculate delay for next attempt
                    if attempt < config.max_attempts:
                        delay = config.calculate_delay(attempt)

                        # Check budget before sleeping
                        if not config.budget.can_retry(delay):
                            break

                        # Log retry attempt
                        error_logger.log_retry_attempt(
                            error,
                            attempt,
                            config.max_attempts,
                            delay,
                            context={"function": func.__name__},
                        )

                        # Consume delay from budget and sleep
                        config.budget.consume_delay(delay)
                        await asyncio.sleep(delay)

            # Re-raise the last error
            if last_error:
                # Log retry exhaustion if we tried multiple times
                if attempt > 1:
                    error_logger.log_retry_exhausted(
                        last_error, attempt, context={"function": func.__name__}
                    )
                raise last_error

        return wrapper

    return decorator
