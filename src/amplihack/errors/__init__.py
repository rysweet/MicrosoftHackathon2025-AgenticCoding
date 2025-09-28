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
from .logging import (
    CorrelationFilter,
    ErrorLogger,
    clear_correlation_id,
    generate_correlation_id,
    get_correlation_id,
    log_error,
    set_correlation_id,
)
from .retry import RetryBudget, RetryConfig, retry_async, retry_on_error
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
    "RetryBudget",
    # Logging
    "ErrorLogger",
    "log_error",
    "CorrelationFilter",
    # Correlation IDs
    "set_correlation_id",
    "get_correlation_id",
    "clear_correlation_id",
    "generate_correlation_id",
    # Security
    "sanitize_error_message",
    "sanitize_path",
    # Templates
    "ERROR_TEMPLATES",
    "format_error_message",
    "format_process_error",
]
