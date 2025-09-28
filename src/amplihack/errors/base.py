"""Base error classes for amplihack error handling."""

from typing import Any, Dict, Optional


class AmplihackError(Exception):
    """Base exception for all amplihack-related errors."""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Initialize amplihack error.

        Args:
            message: Human-readable error message
            context: Additional context information
        """
        super().__init__(message)
        self.context = context or {}


class ValidationError(AmplihackError):
    """Raised when input validation fails."""
    pass


class ConfigurationError(AmplihackError):
    """Raised when configuration is invalid or missing."""
    pass


class ProcessError(AmplihackError):
    """Raised when process operations fail."""

    def __init__(self, message: str, return_code: Optional[int] = None, **kwargs):
        """Initialize process error.

        Args:
            message: Error message
            return_code: Process return code
            **kwargs: Additional arguments for base class
        """
        super().__init__(message, **kwargs)
        self.return_code = return_code


class NetworkError(AmplihackError):
    """Raised when network operations fail."""
    pass


class SecurityError(AmplihackError):
    """Raised when security violations are detected."""
    pass


class TimeoutError(AmplihackError):
    """Raised when operations timeout."""
    pass