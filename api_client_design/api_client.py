"""
REST API Client Library - Public Interface

Philosophy:
- Single responsibility: Each class has ONE purpose
- Ruthless simplicity: No unnecessary abstractions
- Zero-BS: Every method works or doesn't exist
- Regeneratable: Can be rebuilt from specification

Public API (the "studs"):
    APIClient: Main client for HTTP operations
    Request: HTTP request representation
    Response: HTTP response representation
    RetryConfig: Retry behavior configuration
    RateLimiter: Rate limiting interface
    Exceptions: APIError hierarchy
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Union, Protocol
from enum import Enum
import time

__all__ = [
    # Main client
    "APIClient",

    # Data models
    "Request",
    "Response",
    "HTTPMethod",

    # Configuration
    "RetryConfig",
    "RateLimiter",

    # Exceptions
    "APIError",
    "HTTPError",
    "ConnectionError",
    "TimeoutError",
    "RateLimitError",
]


# ============================================================================
# HTTP Methods
# ============================================================================

class HTTPMethod(str, Enum):
    """Supported HTTP methods"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


# ============================================================================
# Request/Response Models
# ============================================================================

@dataclass
class Request:
    """HTTP request representation - immutable after creation"""
    method: HTTPMethod
    path: str
    headers: Dict[str, str] = field(default_factory=dict)
    params: Dict[str, str] = field(default_factory=dict)
    json: Optional[Dict[str, Any]] = None
    data: Optional[Union[str, bytes]] = None
    timeout: Optional[float] = None

    def __post_init__(self):
        """Validate request data"""
        if self.json is not None and self.data is not None:
            raise ValueError("Cannot specify both json and data")
        if not self.path.startswith("/"):
            self.path = "/" + self.path


@dataclass
class Response:
    """HTTP response representation - immutable after creation"""
    status_code: int
    headers: Dict[str, str]
    text: str
    request: Request
    elapsed: float
    _json_cache: Optional[Dict[str, Any]] = field(default=None, init=False)

    @property
    def json(self) -> Dict[str, Any]:
        """Parse JSON response lazily"""
        if self._json_cache is None:
            import json
            self._json_cache = json.loads(self.text)
        return self._json_cache

    @property
    def ok(self) -> bool:
        """Check if response was successful"""
        return 200 <= self.status_code < 300


# ============================================================================
# Configuration Interfaces
# ============================================================================

@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_retries: int = 3
    backoff_factor: float = 1.0
    retry_on_status: tuple[int, ...] = (429, 500, 502, 503, 504)

    def should_retry(self, status_code: int, attempt: int) -> bool:
        """Determine if request should be retried"""
        return attempt < self.max_retries and status_code in self.retry_on_status

    def get_backoff_time(self, attempt: int) -> float:
        """Calculate exponential backoff time"""
        return self.backoff_factor * (2 ** attempt)


class RateLimiter(Protocol):
    """Protocol for rate limiting implementations"""

    def acquire(self) -> None:
        """Block until request can be made within rate limits"""
        ...

    def reset(self) -> None:
        """Reset rate limiter state"""
        ...


@dataclass
class SimpleRateLimiter:
    """Simple token bucket rate limiter"""
    requests_per_second: float
    burst_size: int = 1
    _last_request: float = field(default=0.0, init=False)
    _tokens: float = field(default=0.0, init=False)

    def __post_init__(self):
        self._tokens = float(self.burst_size)

    def acquire(self) -> None:
        """Wait until request can be made"""
        now = time.time()

        # Replenish tokens
        if self._last_request > 0:
            elapsed = now - self._last_request
            self._tokens = min(
                self.burst_size,
                self._tokens + elapsed * self.requests_per_second
            )

        # Wait if no tokens available
        if self._tokens < 1:
            wait_time = (1 - self._tokens) / self.requests_per_second
            time.sleep(wait_time)
            self._tokens = 1

        self._tokens -= 1
        self._last_request = time.time()

    def reset(self) -> None:
        """Reset to full burst capacity"""
        self._tokens = float(self.burst_size)
        self._last_request = 0.0


# ============================================================================
# Exception Hierarchy
# ============================================================================

class APIError(Exception):
    """Base exception for all API errors"""
    def __init__(
        self,
        message: str,
        request: Optional[Request] = None,
        response: Optional[Response] = None
    ):
        super().__init__(message)
        self.message = message
        self.request = request
        self.response = response


class HTTPError(APIError):
    """HTTP response error (4xx, 5xx)"""
    def __init__(
        self,
        status_code: int,
        message: str,
        request: Request,
        response: Response
    ):
        super().__init__(message, request, response)
        self.status_code = status_code


class ConnectionError(APIError):
    """Network connection error"""
    def __init__(self, message: str, cause: str, request: Request):
        super().__init__(message, request)
        self.cause = cause


class TimeoutError(APIError):
    """Request timeout error"""
    def __init__(self, timeout: float, request: Request):
        message = f"Request timed out after {timeout} seconds"
        super().__init__(message, request)
        self.timeout = timeout


class RateLimitError(HTTPError):
    """Rate limit exceeded error"""
    def __init__(self, retry_after: float, request: Request, response: Response):
        message = f"Rate limit exceeded. Retry after {retry_after} seconds"
        super().__init__(429, message, request, response)
        self.retry_after = retry_after


# ============================================================================
# Main Client Interface
# ============================================================================

class APIClient:
    """
    Main REST API client

    Usage:
        client = APIClient("https://api.example.com")
        response = client.get("/users", params={"limit": 10})

        # With configuration
        client = APIClient(
            base_url="https://api.example.com",
            timeout=30,
            retry_config=RetryConfig(max_retries=5),
            rate_limiter=SimpleRateLimiter(requests_per_second=10)
        )
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        retry_config: Optional[RetryConfig] = None,
        rate_limiter: Optional[RateLimiter] = None,
        default_headers: Optional[Dict[str, str]] = None
    ):
        """Initialize API client with base configuration"""
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retry_config = retry_config or RetryConfig()
        self.rate_limiter = rate_limiter
        self.default_headers = default_headers or {}

        # Validate URL
        if not self.base_url.startswith(("http://", "https://")):
            raise ValueError(f"Invalid base_url: {base_url}")

    # ========================================================================
    # Public HTTP Methods
    # ========================================================================

    def get(
        self,
        path: str,
        *,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> Response:
        """GET request"""
        request = Request(
            method=HTTPMethod.GET,
            path=path,
            params=params or {},
            headers=self._merge_headers(headers),
            timeout=timeout or self.timeout
        )
        return self._execute(request)

    def post(
        self,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Union[str, bytes]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> Response:
        """POST request"""
        request = Request(
            method=HTTPMethod.POST,
            path=path,
            json=json,
            data=data,
            headers=self._merge_headers(headers),
            timeout=timeout or self.timeout
        )
        return self._execute(request)

    def put(
        self,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Union[str, bytes]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> Response:
        """PUT request"""
        request = Request(
            method=HTTPMethod.PUT,
            path=path,
            json=json,
            data=data,
            headers=self._merge_headers(headers),
            timeout=timeout or self.timeout
        )
        return self._execute(request)

    def delete(
        self,
        path: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> Response:
        """DELETE request"""
        request = Request(
            method=HTTPMethod.DELETE,
            path=path,
            headers=self._merge_headers(headers),
            timeout=timeout or self.timeout
        )
        return self._execute(request)

    def patch(
        self,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Union[str, bytes]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> Response:
        """PATCH request"""
        request = Request(
            method=HTTPMethod.PATCH,
            path=path,
            json=json,
            data=data,
            headers=self._merge_headers(headers),
            timeout=timeout or self.timeout
        )
        return self._execute(request)

    def request(self, request: Request) -> Response:
        """Execute arbitrary request"""
        return self._execute(request)

    # ========================================================================
    # Extension Points (Protected Methods)
    # ========================================================================

    def _merge_headers(self, headers: Optional[Dict[str, str]]) -> Dict[str, str]:
        """Merge request headers with defaults"""
        result = self.default_headers.copy()
        if headers:
            result.update(headers)
        return result

    def _execute(self, request: Request) -> Response:
        """
        Execute HTTP request with retry and rate limiting

        Extension point: Override this to customize execution
        """
        # Rate limiting
        if self.rate_limiter:
            self.rate_limiter.acquire()

        # Retry loop
        last_error = None
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                response = self._send_request(request)

                # Check for HTTP errors
                if not response.ok:
                    if self.retry_config.should_retry(response.status_code, attempt):
                        # Check for rate limit with Retry-After
                        if response.status_code == 429:
                            retry_after = float(
                                response.headers.get("Retry-After",
                                                   self.retry_config.get_backoff_time(attempt))
                            )
                            if attempt == self.retry_config.max_retries:
                                raise RateLimitError(retry_after, request, response)
                            time.sleep(retry_after)
                            continue

                        # Regular retry with backoff
                        time.sleep(self.retry_config.get_backoff_time(attempt))
                        continue

                    # Non-retryable HTTP error
                    raise HTTPError(
                        response.status_code,
                        f"HTTP {response.status_code}: {response.text[:200]}",
                        request,
                        response
                    )

                return response

            except (ConnectionError, TimeoutError) as e:
                last_error = e
                if attempt < self.retry_config.max_retries:
                    time.sleep(self.retry_config.get_backoff_time(attempt))
                    continue
                raise

        # Exhausted retries
        if last_error:
            raise last_error
        raise APIError("Request failed after retries", request)

    def _send_request(self, request: Request) -> Response:
        """
        Send single HTTP request (no retry logic)

        Extension point: Override this to use different HTTP library
        """
        # This is a stub - would use requests, httpx, or urllib3
        # For now, create a mock response to demonstrate the interface
        import time
        start = time.time()

        # Simulate network call
        time.sleep(0.01)

        # Mock response for demonstration
        return Response(
            status_code=200,
            headers={"Content-Type": "application/json"},
            text='{"status": "ok"}',
            request=request,
            elapsed=time.time() - start
        )