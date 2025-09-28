"""Data models for rate limiting system."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Optional


class RateLimitStatus(Enum):
    """Status of rate limit operation."""

    SUCCESS = "success"
    RETRY = "retry"
    EXHAUSTED = "exhausted"
    ERROR = "error"


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting behavior.

    Attributes:
        initial_tokens: Starting token capacity (default: 1000)
        refill_rate: Tokens added per minute (default: 100)
        max_retries: Maximum retry attempts (default: 5)
        initial_delay: Initial backoff delay in seconds (default: 1.0)
        max_delay: Maximum backoff delay in seconds (default: 60.0)
        jitter_factor: Randomization factor for jitter (default: 0.1 = ±10%)
        backoff_multiplier: Exponential backoff multiplier (default: 2.0)
    """

    initial_tokens: int = 1000
    refill_rate: float = 100.0  # tokens per minute
    max_retries: int = 5
    initial_delay: float = 1.0
    max_delay: float = 60.0
    jitter_factor: float = 0.1
    backoff_multiplier: float = 2.0

    def __post_init__(self):
        """Validate configuration parameters."""
        if self.initial_tokens <= 0:
            raise ValueError("initial_tokens must be positive")
        if self.refill_rate <= 0:
            raise ValueError("refill_rate must be positive")
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if self.initial_delay <= 0:
            raise ValueError("initial_delay must be positive")
        if self.max_delay < self.initial_delay:
            raise ValueError("max_delay must be >= initial_delay")
        if not 0 <= self.jitter_factor < 1:
            raise ValueError("jitter_factor must be in range [0, 1)")
        if self.backoff_multiplier <= 1:
            raise ValueError("backoff_multiplier must be > 1")


@dataclass
class RateLimitState:
    """Current state of rate limiting system.

    Tracks the current state including tokens, retries, and timing.
    """

    current_tokens: float
    last_refill: datetime
    retry_count: int = 0
    last_delay: float = 0.0
    consecutive_successes: int = 0
    consecutive_failures: int = 0
    total_requests: int = 0
    total_retries: int = 0

    def reset_backoff(self):
        """Reset backoff state after success."""
        self.retry_count = 0
        self.last_delay = 0.0
        self.consecutive_failures = 0
        self.consecutive_successes += 1

    def increment_retry(self):
        """Increment retry counter."""
        self.retry_count += 1
        self.total_retries += 1
        self.consecutive_failures += 1
        self.consecutive_successes = 0

    def record_request(self):
        """Record a request attempt."""
        self.total_requests += 1


@dataclass
class RetryContext:
    """Context for a retry operation.

    Contains all information needed to execute and track a retry.
    """

    attempt: int
    delay: float
    tokens_available: float
    tokens_required: float = 1.0
    reason: Optional[str] = None
    error: Optional[Exception] = None

    @property
    def should_retry(self) -> bool:
        """Check if retry should proceed."""
        return self.tokens_available >= self.tokens_required


@dataclass
class RetryResult:
    """Result of a retry operation."""

    status: RateLimitStatus
    value: Optional[Any] = None
    error: Optional[Exception] = None
    attempts: int = 0
    total_delay: float = 0.0
    tokens_consumed: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        """Check if operation succeeded."""
        return self.status == RateLimitStatus.SUCCESS

    @property
    def failed(self) -> bool:
        """Check if operation failed permanently."""
        return self.status in (RateLimitStatus.EXHAUSTED, RateLimitStatus.ERROR)


@dataclass
class ProgressUpdate:
    """Progress update for user feedback."""

    attempt: int
    max_attempts: int
    delay: float
    tokens_remaining: float
    estimated_wait: Optional[float] = None
    message: Optional[str] = None

    def format_message(self) -> str:
        """Format progress message for display."""
        parts = [f"Attempt {self.attempt}/{self.max_attempts}"]

        if self.delay > 0:
            parts.append(f"waiting {self.delay:.1f}s")

        parts.append(f"{self.tokens_remaining:.0f} tokens remaining")

        if self.estimated_wait:
            parts.append(f"~{self.estimated_wait:.1f}s total wait")

        if self.message:
            parts.append(f"({self.message})")

        return " - ".join(parts)


class RateLimitException(Exception):
    """Base exception for rate limiting errors."""

    pass


class RateLimitExhausted(RateLimitException):
    """Raised when rate limit retries are exhausted."""

    def __init__(self, attempts: int, total_delay: float, last_error: Optional[Exception] = None):
        self.attempts = attempts
        self.total_delay = total_delay
        self.last_error = last_error
        message = f"Rate limit exhausted after {attempts} attempts ({total_delay:.1f}s total delay)"
        if last_error:
            message += f": {last_error}"
        super().__init__(message)


class TokenBudgetExceeded(RateLimitException):
    """Raised when token budget is exceeded and cannot refill in time."""

    def __init__(self, required: float, available: float):
        self.required = required
        self.available = available
        super().__init__(f"Token budget exceeded: {required} required, {available} available")


# Type hints for callbacks
ProgressCallback = Callable[[ProgressUpdate], None]
RetryPredicate = Callable[[Exception], bool]
