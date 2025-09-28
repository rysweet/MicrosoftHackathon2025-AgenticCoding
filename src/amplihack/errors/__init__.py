"""Simple error handling infrastructure for amplihack."""

from .base import (
    AmplihackError,
    ConfigurationError,
    NetworkError,
    ProcessError,
    SecurityError,
    TimeoutError,
    ValidationError,
)
from .logging import ErrorLogger, log_error
from .retry import RetryConfig, retry_on_error, retry_async
from .security import sanitize_error_message, sanitize_path
from .templates import ERROR_TEMPLATES, format_error_message, format_process_error

__all__ = [
    # Base error classes
    "AmplihackError",
    "ConfigurationError",
    "NetworkError",
    "ProcessError",
    "SecurityError",
    "TimeoutError",
    "ValidationError",
    # Retry functionality
    "retry_on_error",
    "retry_async",
    "RetryConfig",
    # Logging
    "ErrorLogger",
    "log_error",
    # Security
    "sanitize_error_message",
    "sanitize_path",
    # Templates
    "ERROR_TEMPLATES",
    "format_error_message",
    "format_process_error",
]