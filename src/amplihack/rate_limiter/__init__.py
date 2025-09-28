"""Rate limiting protection system for API calls.

This module provides comprehensive rate limiting with exponential backoff
and token budget management for protecting against API overload.
"""

from .backoff import AdaptiveBackoff, ExponentialBackoff, wait_with_progress
from .core import RateLimiter, rate_limit
from .models import (
    ProgressCallback,
    ProgressUpdate,
    RateLimitConfig,
    RateLimitException,
    RateLimitExhausted,
    RateLimitState,
    RateLimitStatus,
    RetryContext,
    RetryPredicate,
    RetryResult,
    TokenBudgetExceeded,
)
from .token_budget import LeakyBucket, SlidingWindowCounter, TokenBucket

__all__ = [
    # Core functionality
    "RateLimiter",
    "rate_limit",
    # Configuration and models
    "RateLimitConfig",
    "RateLimitState",
    "RateLimitStatus",
    "RetryContext",
    "RetryResult",
    "ProgressUpdate",
    # Exceptions
    "RateLimitException",
    "RateLimitExhausted",
    "TokenBudgetExceeded",
    # Type hints
    "ProgressCallback",
    "RetryPredicate",
    # Advanced components (for custom implementations)
    "ExponentialBackoff",
    "AdaptiveBackoff",
    "TokenBucket",
    "LeakyBucket",
    "SlidingWindowCounter",
    "wait_with_progress",
]

__version__ = "1.0.0"
