"""Simple error logging framework."""

import logging
import threading
import uuid
from typing import Any, Dict, Optional


class ErrorLogger:
    """Simple error logger."""

    def __init__(self, name: str = "amplihack.errors"):
        """Initialize error logger.

        Args:
            name: Logger name
        """
        self.logger = logging.getLogger(name)

    def log_error(
        self,
        error: Exception,
        level: int = logging.ERROR,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log an error with context.

        Args:
            error: Exception to log
            level: Logging level
            context: Additional context
        """
        message = f"Error: {error.__class__.__name__}: {error}"
        if context:
            message += f" | Context: {context}"
        self.logger.log(level, message)


# Global error logger instance
error_logger = ErrorLogger()


def log_error(
    error: Exception,
    level: int = logging.ERROR,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """Convenience function to log errors using global logger.

    Args:
        error: Exception to log
        level: Logging level
        context: Additional context
    """
    error_logger.log_error(error, level, context)


# Thread-local storage for correlation IDs
_local = threading.local()


def generate_correlation_id() -> str:
    """Generate a new correlation ID.

    Returns:
        New UUID-based correlation ID
    """
    return str(uuid.uuid4())[:8]


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """Set correlation ID for current thread.

    Args:
        correlation_id: Correlation ID to set, or None to generate new one

    Returns:
        The correlation ID that was set
    """
    if correlation_id is None:
        correlation_id = generate_correlation_id()
    _local.correlation_id = correlation_id
    return correlation_id


def get_correlation_id() -> Optional[str]:
    """Get correlation ID for current thread.

    Returns:
        Current correlation ID or None if not set
    """
    return getattr(_local, "correlation_id", None)


def clear_correlation_id() -> None:
    """Clear correlation ID for current thread."""
    if hasattr(_local, "correlation_id"):
        delattr(_local, "correlation_id")


class CorrelationFilter(logging.Filter):
    """Logging filter that adds correlation ID to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to log record.

        Args:
            record: Log record to modify

        Returns:
            True to include the record in output
        """
        correlation_id = get_correlation_id()
        record.correlation_id = correlation_id or "none"
        return True
