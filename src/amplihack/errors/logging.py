"""Simple error logging framework."""

import logging
from typing import Any, Dict, Optional


class ErrorLogger:
    """Simple error logger."""

    def __init__(self, name: str = 'amplihack.errors'):
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