"""Basic security utilities for error handling."""

import re
from pathlib import Path


def sanitize_error_message(message: str) -> str:
    """Sanitize error message to remove sensitive information.

    Args:
        message: Original error message

    Returns:
        Sanitized error message with credentials removed
    """
    if not message:
        return message

    # Basic patterns to sanitize
    patterns = [
        (r'api[_-]?key[=:\s]+["\']?[a-zA-Z0-9_-]{10,}["\']?', r"api_key=***"),
        (r'token[=:\s]+["\']?[a-zA-Z0-9_.-]{20,}["\']?', r"token=***"),
        (r'password[=:\s]+["\']?[^\s"\']{8,}["\']?', r"password=***"),
        (r"/Users/[^/\s]+", r"/Users/***"),
        (r"/home/[^/\s]+", r"/home/***"),
    ]

    sanitized = message
    for pattern, replacement in patterns:
        sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)

    return sanitized


def sanitize_path(path: str) -> str:
    """Sanitize file path to remove sensitive information.

    Args:
        path: Original file path

    Returns:
        Sanitized path with user-specific information removed
    """
    if not path:
        return path

    try:
        # Replace home directory with placeholder
        p = Path(path)
        home = Path.home()
        if p.is_relative_to(home):
            relative = p.relative_to(home)
            return f"~/{relative}"
    except (ValueError, OSError):
        pass

    # Basic path sanitization
    path_str = re.sub(r"/Users/[^/]+", "/Users/***", path)
    path_str = re.sub(r"/home/[^/]+", "/home/***", path_str)
    return path_str
