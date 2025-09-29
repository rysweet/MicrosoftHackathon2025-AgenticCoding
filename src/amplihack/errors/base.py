"""Base error classes for amplihack error handling."""

from typing import Any, Dict, Optional


class AmplihackError(Exception):
    """Base exception for all amplihack-related errors."""

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ):
        """Initialize amplihack error.

        Args:
            message: Human-readable error message
            context: Additional context information
            correlation_id: Correlation ID for tracking related errors
        """
        super().__init__(message)
        self.context = context or {}
        self.correlation_id = correlation_id


class ValidationError(AmplihackError):
    """Raised when input validation fails."""

    pass


class ConfigurationError(AmplihackError):
    """Raised when configuration is invalid or missing."""

    pass


class ProcessError(AmplihackError):
    """Raised when process operations fail."""

    def __init__(
        self,
        message: str,
        return_code: Optional[int] = None,
        command: Optional[str] = None,
        **kwargs,
    ):
        """Initialize process error.

        Args:
            message: Error message
            return_code: Process return code
            command: Command that failed
            **kwargs: Additional arguments for base class
        """
        super().__init__(message, **kwargs)
        self.return_code = return_code
        self.command = command


class NetworkError(AmplihackError):
    """Raised when network operations fail."""

    def __init__(self, message: str, timeout: Optional[float] = None, **kwargs):
        """Initialize network error.

        Args:
            message: Error message
            timeout: Timeout duration in seconds
            **kwargs: Additional arguments for base class
        """
        super().__init__(message, **kwargs)
        self.timeout = timeout


class SecurityError(AmplihackError):
    """Raised when security violations are detected."""

    pass


class TimeoutError(AmplihackError):
    """Raised when operations timeout."""

    def __init__(
        self,
        message: str,
        timeout_duration: Optional[float] = None,
        operation: Optional[str] = None,
        **kwargs,
    ):
        """Initialize timeout error.

        Args:
            message: Error message
            timeout_duration: Duration before timeout in seconds
            operation: Operation that timed out
            **kwargs: Additional arguments for base class
        """
        super().__init__(message, **kwargs)
        self.timeout_duration = timeout_duration
        self.operation = operation
