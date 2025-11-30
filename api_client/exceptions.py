"""Exception hierarchy for API client.

Clear, specific exceptions for different failure modes.
All exceptions carry context for debugging and recovery.
"""

from typing import Optional, Dict, Any


class APIException(Exception):
    """Base exception for all API client errors.

    All API exceptions inherit from this base class.
    """

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        response: Optional["Response"] = None
    ) -> None:
        """Initialize API exception with context.

        Args:
            message: Human-readable error message
            code: Machine-readable error code
            details: Additional error context
            response: HTTP response if available
        """
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
        self.response = response


class RateLimitException(APIException):
    """Rate limit exceeded error.

    Raised when API rate limits are hit.
    Check retry_after for wait time.
    """

    def __init__(
        self,
        message: str,
        retry_after: Optional[float] = None,
        **kwargs: Any
    ) -> None:
        """Initialize rate limit exception.

        Args:
            message: Error message
            retry_after: Seconds to wait before retry
            **kwargs: Additional context
        """
        super().__init__(message, code="RATE_LIMIT_EXCEEDED", **kwargs)
        self.retry_after = retry_after
        if retry_after:
            self.details["retry_after"] = retry_after


class TimeoutException(APIException):
    """Request timeout error.

    Raised when a request exceeds the timeout duration.
    """

    def __init__(
        self,
        message: str,
        timeout: Optional[float] = None,
        **kwargs: Any
    ) -> None:
        """Initialize timeout exception.

        Args:
            message: Error message
            timeout: Timeout value that was exceeded
            **kwargs: Additional context
        """
        super().__init__(message, code="REQUEST_TIMEOUT", **kwargs)
        self.timeout = timeout
        if timeout:
            self.details["timeout"] = timeout


class NetworkException(APIException):
    """Network connectivity error.

    Raised for network-level failures (DNS, connection, etc).
    """

    def __init__(
        self,
        message: str,
        original_error: Optional[Exception] = None,
        **kwargs: Any
    ) -> None:
        """Initialize network exception.

        Args:
            message: Error message
            original_error: Underlying network exception
            **kwargs: Additional context
        """
        super().__init__(message, code="NETWORK_ERROR", **kwargs)
        self.original_error = original_error
        if original_error:
            self.details["original_error"] = str(original_error)


class ValidationException(APIException):
    """Request/response validation error.

    Raised for client-side errors (4xx status codes).
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        **kwargs: Any
    ) -> None:
        """Initialize validation exception.

        Args:
            message: Error message
            status_code: HTTP status code
            **kwargs: Additional context
        """
        super().__init__(message, code="VALIDATION_ERROR", **kwargs)
        self.status_code = status_code
        if status_code:
            self.details["status_code"] = status_code


class ServerException(APIException):
    """Server-side error (5xx status codes).

    Raised for server failures that might be retryable.
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        **kwargs: Any
    ) -> None:
        """Initialize server exception.

        Args:
            message: Error message
            status_code: HTTP status code
            **kwargs: Additional context
        """
        super().__init__(message, code="SERVER_ERROR", **kwargs)
        self.status_code = status_code
        if status_code:
            self.details["status_code"] = status_code