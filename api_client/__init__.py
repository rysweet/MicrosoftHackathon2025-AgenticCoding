"""REST API Client Library - Public Interface.

Philosophy:
- Single responsibility: HTTP client operations
- Standard library + minimal dependencies (httpx for async)
- Self-contained and regeneratable from OpenAPI spec

Public API (the "studs"):
    APIClient: Main client class for making HTTP requests
    Request: Request data model
    Response: Response data model
    APIException: Base exception for all API errors
    RateLimitException: Rate limit exceeded error
    TimeoutException: Request timeout error
    NetworkException: Network connectivity error
    ValidationException: Request/response validation error
    ServerException: Server-side error (5xx)
    RetryConfig: Retry behavior configuration
    RateLimitConfig: Rate limiting configuration
"""

from .client import APIClient
from .models import Request, Response
from .exceptions import (
    APIException,
    RateLimitException,
    TimeoutException,
    NetworkException,
    ValidationException,
    ServerException
)
from .config import RetryConfig, RateLimitConfig

__all__ = [
    # Main client
    "APIClient",

    # Data models
    "Request",
    "Response",

    # Exception hierarchy
    "APIException",
    "RateLimitException",
    "TimeoutException",
    "NetworkException",
    "ValidationException",
    "ServerException",

    # Configuration
    "RetryConfig",
    "RateLimitConfig",
]

__version__ = "1.0.0"