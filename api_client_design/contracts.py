"""REST API Client Contracts

Zero-dependency REST client with clear, minimal contracts.
Built on urllib for maximum portability and simplicity.

Philosophy:
- Single purpose per component
- Contracts define the connection points
- Thread-safe by default
- Regeneratable from specification
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Protocol
from enum import Enum
import time


# ============================================================================
# Request/Response Models
# ============================================================================

class HTTPMethod(str, Enum):
    """HTTP methods supported by the client."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


@dataclass
class Request:
    """HTTP request specification.

    Minimal contract for making HTTP requests.
    """
    method: HTTPMethod
    url: str
    headers: Dict[str, str] = field(default_factory=dict)
    params: Optional[Dict[str, str]] = None
    json_body: Optional[Any] = None  # Will be serialized to JSON
    data: Optional[bytes] = None  # Raw bytes for body
    timeout: Optional[float] = None

    def __post_init__(self):
        """Validate request consistency."""
        if self.json_body is not None and self.data is not None:
            raise ValueError("Cannot specify both json_body and data")


@dataclass
class Response:
    """HTTP response container.

    Complete response with all necessary metadata.
    """
    status_code: int
    headers: Dict[str, str]
    body: bytes
    url: str  # Final URL after redirects
    elapsed: float  # Seconds

    def json(self) -> Any:
        """Parse response body as JSON."""
        import json
        return json.loads(self.body.decode('utf-8'))

    def text(self) -> str:
        """Get response body as text."""
        return self.body.decode('utf-8')

    def raise_for_status(self) -> None:
        """Raise exception for 4xx/5xx status codes."""
        if 400 <= self.status_code < 600:
            raise HTTPError(
                f"HTTP {self.status_code}",
                response=self
            )


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class ClientConfig:
    """REST client configuration.

    All client behavior configuration in one place.
    """
    base_url: Optional[str] = None
    default_headers: Dict[str, str] = field(default_factory=dict)
    timeout: float = 30.0
    max_retries: int = 3
    retry_on: List[int] = field(default_factory=lambda: [502, 503, 504])

    def merge_with_request(self, request: Request) -> Request:
        """Merge config defaults with specific request."""
        url = request.url
        if self.base_url and not request.url.startswith(('http://', 'https://')):
            url = self.base_url.rstrip('/') + '/' + request.url.lstrip('/')

        headers = {**self.default_headers, **request.headers}
        timeout = request.timeout if request.timeout is not None else self.timeout

        return Request(
            method=request.method,
            url=url,
            headers=headers,
            params=request.params,
            json_body=request.json_body,
            data=request.data,
            timeout=timeout
        )


# ============================================================================
# Exception Hierarchy
# ============================================================================

class APIClientError(Exception):
    """Base exception for all API client errors."""
    pass


class HTTPError(APIClientError):
    """HTTP error response (4xx/5xx)."""
    def __init__(self, message: str, response: Optional[Response] = None):
        super().__init__(message)
        self.response = response


class ConnectionError(APIClientError):
    """Network connection error."""
    pass


class TimeoutError(APIClientError):
    """Request timeout error."""
    pass


class RetryExhausted(APIClientError):
    """All retry attempts failed."""
    def __init__(self, message: str, last_error: Exception):
        super().__init__(message)
        self.last_error = last_error


# ============================================================================
# Protocol Definitions (Extension Points)
# ============================================================================

class RetryStrategy(Protocol):
    """Protocol for custom retry strategies."""

    def should_retry(self, attempt: int, error: Exception, response: Optional[Response]) -> bool:
        """Determine if request should be retried."""
        ...

    def get_delay(self, attempt: int) -> float:
        """Get delay in seconds before retry."""
        ...


class RequestMiddleware(Protocol):
    """Protocol for request preprocessing."""

    def process_request(self, request: Request) -> Request:
        """Process request before sending."""
        ...


class ResponseMiddleware(Protocol):
    """Protocol for response postprocessing."""

    def process_response(self, response: Response) -> Response:
        """Process response after receiving."""
        ...


# ============================================================================
# Main Client Interface
# ============================================================================

class RESTClient:
    """Thread-safe REST API client.

    Public API:
        - get(url, **kwargs) -> Response
        - post(url, **kwargs) -> Response
        - put(url, **kwargs) -> Response
        - delete(url, **kwargs) -> Response
        - patch(url, **kwargs) -> Response
        - head(url, **kwargs) -> Response
        - options(url, **kwargs) -> Response
        - request(request: Request) -> Response

    Configuration:
        - __init__(config: ClientConfig)
        - with_config(**kwargs) -> RESTClient  # Returns new configured instance

    Extension Points:
        - add_request_middleware(middleware: RequestMiddleware)
        - add_response_middleware(middleware: ResponseMiddleware)
        - set_retry_strategy(strategy: RetryStrategy)
    """

    def __init__(self, config: Optional[ClientConfig] = None):
        """Initialize with optional configuration."""
        self.config = config or ClientConfig()
        self._request_middleware: List[RequestMiddleware] = []
        self._response_middleware: List[ResponseMiddleware] = []
        self._retry_strategy: Optional[RetryStrategy] = None

    # HTTP method shortcuts
    def get(self, url: str, **kwargs) -> Response:
        """GET request."""
        return self.request(Request(HTTPMethod.GET, url, **kwargs))

    def post(self, url: str, **kwargs) -> Response:
        """POST request."""
        return self.request(Request(HTTPMethod.POST, url, **kwargs))

    def put(self, url: str, **kwargs) -> Response:
        """PUT request."""
        return self.request(Request(HTTPMethod.PUT, url, **kwargs))

    def delete(self, url: str, **kwargs) -> Response:
        """DELETE request."""
        return self.request(Request(HTTPMethod.DELETE, url, **kwargs))

    def patch(self, url: str, **kwargs) -> Response:
        """PATCH request."""
        return self.request(Request(HTTPMethod.PATCH, url, **kwargs))

    def head(self, url: str, **kwargs) -> Response:
        """HEAD request."""
        return self.request(Request(HTTPMethod.HEAD, url, **kwargs))

    def options(self, url: str, **kwargs) -> Response:
        """OPTIONS request."""
        return self.request(Request(HTTPMethod.OPTIONS, url, **kwargs))

    def request(self, request: Request) -> Response:
        """Execute HTTP request with retry logic."""
        raise NotImplementedError("Implementation in api_client module")

    def with_config(self, **kwargs) -> 'RESTClient':
        """Create new client with modified configuration."""
        config_dict = self.config.__dict__.copy()
        config_dict.update(kwargs)
        return RESTClient(ClientConfig(**config_dict))

    def add_request_middleware(self, middleware: RequestMiddleware) -> None:
        """Add request preprocessing middleware."""
        self._request_middleware.append(middleware)

    def add_response_middleware(self, middleware: ResponseMiddleware) -> None:
        """Add response postprocessing middleware."""
        self._response_middleware.append(middleware)

    def set_retry_strategy(self, strategy: RetryStrategy) -> None:
        """Set custom retry strategy."""
        self._retry_strategy = strategy


# ============================================================================
# Public API Exports
# ============================================================================

__all__ = [
    # Main client
    'RESTClient',

    # Configuration
    'ClientConfig',

    # Models
    'Request',
    'Response',
    'HTTPMethod',

    # Exceptions
    'APIClientError',
    'HTTPError',
    'ConnectionError',
    'TimeoutError',
    'RetryExhausted',

    # Extension protocols
    'RetryStrategy',
    'RequestMiddleware',
    'ResponseMiddleware',
]