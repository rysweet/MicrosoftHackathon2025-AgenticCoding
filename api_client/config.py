"""Configuration interfaces for retry and rate limiting.

Immutable configuration objects with validation.
Thread-safe through immutability.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass(frozen=True)
class RetryConfig:
    """Configuration for retry behavior.

    Immutable configuration for automatic retries on failure.
    """
    max_retries: int = 3
    backoff_factor: float = 2.0
    retry_on_status: List[int] = field(default_factory=lambda: [429, 500, 502, 503, 504])

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if self.max_retries > 10:
            raise ValueError("max_retries must not exceed 10")
        if self.backoff_factor < 1.0:
            raise ValueError("backoff_factor must be at least 1.0")

    def calculate_backoff(self, attempt: int) -> float:
        """Calculate backoff time for given attempt.

        Args:
            attempt: Attempt number (0-based)

        Returns:
            Seconds to wait before retry
        """
        if attempt == 0:
            return 0.0
        return min(self.backoff_factor ** (attempt - 1), 60.0)  # Cap at 60 seconds

    def should_retry(self, status_code: int) -> bool:
        """Check if status code should trigger retry.

        Args:
            status_code: HTTP status code

        Returns:
            True if should retry
        """
        return status_code in self.retry_on_status


@dataclass(frozen=True)
class RateLimitConfig:
    """Configuration for rate limiting.

    Immutable configuration for client-side rate limiting.
    Uses token bucket algorithm for burst support.
    """
    requests_per_second: float = 10.0
    burst_size: int = 10

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.requests_per_second <= 0:
            raise ValueError("requests_per_second must be positive")
        if self.requests_per_second > 1000:
            raise ValueError("requests_per_second must not exceed 1000")
        if self.burst_size < 1:
            raise ValueError("burst_size must be at least 1")

    @property
    def refill_period(self) -> float:
        """Calculate token refill period in seconds.

        Returns:
            Seconds between token refills
        """
        return 1.0 / self.requests_per_second

    @property
    def tokens_per_refill(self) -> float:
        """Calculate tokens added per refill.

        Returns:
            Number of tokens to add
        """
        return 1.0


@dataclass(frozen=True)
class APIClientConfig:
    """Complete configuration for API client.

    Immutable configuration combining all settings.
    """
    base_url: str
    timeout: float = 30.0
    retry_config: RetryConfig = field(default_factory=RetryConfig)
    rate_limit_config: Optional[RateLimitConfig] = None
    headers: Dict[str, str] = field(default_factory=dict)
    verify_ssl: bool = True
    follow_redirects: bool = True

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if not self.base_url:
            raise ValueError("base_url is required")
        if not self.base_url.startswith(("http://", "https://")):
            raise ValueError("base_url must start with http:// or https://")
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")

        # Remove trailing slash from base_url for consistency
        if self.base_url.endswith("/"):
            object.__setattr__(self, "base_url", self.base_url.rstrip("/"))

    def with_headers(self, **headers: str) -> "APIClientConfig":
        """Create new config with additional headers.

        Args:
            **headers: Headers to add/override

        Returns:
            New configuration instance
        """
        new_headers = {**self.headers, **headers}
        return APIClientConfig(
            base_url=self.base_url,
            timeout=self.timeout,
            retry_config=self.retry_config,
            rate_limit_config=self.rate_limit_config,
            headers=new_headers,
            verify_ssl=self.verify_ssl,
            follow_redirects=self.follow_redirects
        )