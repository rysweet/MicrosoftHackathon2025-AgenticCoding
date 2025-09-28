"""Retry decorator with exponential backoff."""

import functools
import random
import time
from typing import Any, Callable, Optional, Tuple, Type

from .base import TimeoutError
from .logging import log_error


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        retryable_errors: Optional[Tuple[Type[Exception], ...]] = None,
    ):
        """Initialize retry configuration.

        Args:
            max_attempts: Maximum number of retry attempts
            base_delay: Base delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            retryable_errors: Tuple of exception types that should trigger retries
        """
        self.max_attempts = max(1, min(max_attempts, 5))  # Limit 1-5 attempts
        self.base_delay = max(0.1, base_delay)
        self.max_delay = min(max_delay, 30.0)  # Max 30 seconds

        # Default retryable errors (network, temporary failures)
        self.retryable_errors = retryable_errors or (
            ConnectionError,
            TimeoutError,
            OSError,
        )

        # Non-retryable errors (validation, security, permanent failures)
        self.non_retryable_errors = (
            ValueError,
            TypeError,
            KeyboardInterrupt,
            SystemExit,
        )

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt.

        Args:
            attempt: Attempt number (1-based)

        Returns:
            Delay in seconds
        """
        if attempt <= 0:
            return 0.0

        # Exponential backoff: base_delay * (2 ^ (attempt - 1))
        delay = self.base_delay * (2 ** (attempt - 1))
        delay = min(delay, self.max_delay)

        # Add jitter (±25% of delay)
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
                        time.sleep(delay)

            # Re-raise the last error
            if last_error:
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
                        await asyncio.sleep(delay)

            # Re-raise the last error
            if last_error:
                raise last_error

        return wrapper

    return decorator
