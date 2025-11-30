"""Request and Response data models.

Clean, immutable data structures for API operations.
All models are thread-safe through immutability.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Literal, Union
from datetime import datetime

# HTTP method type
HTTPMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]


@dataclass(frozen=True)
class Request:
    """Immutable HTTP request model.

    Thread-safe through immutability. Create new instances for modifications.
    """
    method: HTTPMethod
    path: str
    params: Optional[Dict[str, Any]] = field(default_factory=dict)
    headers: Optional[Dict[str, str]] = field(default_factory=dict)
    json_data: Optional[Dict[str, Any]] = None
    data: Optional[bytes] = None
    timeout: Optional[float] = None

    def __post_init__(self) -> None:
        """Validate request after initialization."""
        if self.json_data is not None and self.data is not None:
            raise ValueError("Cannot specify both json_data and data")

        if not self.path.startswith("/"):
            # Force path to start with /
            object.__setattr__(self, "path", f"/{self.path}")

    def with_headers(self, **headers: str) -> "Request":
        """Create new request with additional headers."""
        new_headers = {**(self.headers or {}), **headers}
        return Request(
            method=self.method,
            path=self.path,
            params=self.params,
            headers=new_headers,
            json_data=self.json_data,
            data=self.data,
            timeout=self.timeout
        )

    def with_params(self, **params: Any) -> "Request":
        """Create new request with additional query parameters."""
        new_params = {**(self.params or {}), **params}
        return Request(
            method=self.method,
            path=self.path,
            params=new_params,
            headers=self.headers,
            json_data=self.json_data,
            data=self.data,
            timeout=self.timeout
        )


@dataclass(frozen=True)
class Response:
    """Immutable HTTP response model.

    Thread-safe through immutability. Stores response data and metadata.
    """
    status_code: int
    headers: Dict[str, str]
    json_data: Optional[Dict[str, Any]] = None
    text: Optional[str] = None
    elapsed: float = 0.0
    request: Optional[Request] = None
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def is_success(self) -> bool:
        """Check if response indicates success (2xx status)."""
        return 200 <= self.status_code < 300

    @property
    def is_error(self) -> bool:
        """Check if response indicates an error (4xx or 5xx)."""
        return self.status_code >= 400

    @property
    def is_client_error(self) -> bool:
        """Check if response indicates client error (4xx)."""
        return 400 <= self.status_code < 500

    @property
    def is_server_error(self) -> bool:
        """Check if response indicates server error (5xx)."""
        return 500 <= self.status_code < 600

    def raise_for_status(self) -> None:
        """Raise exception for 4xx/5xx status codes."""
        from .exceptions import ValidationException, ServerException

        if self.is_client_error:
            raise ValidationException(
                f"Client error {self.status_code}",
                status_code=self.status_code,
                response=self
            )
        elif self.is_server_error:
            raise ServerException(
                f"Server error {self.status_code}",
                status_code=self.status_code,
                response=self
            )