"""Simple error message formatting utilities."""

from typing import Any, Dict, Optional

from .security import sanitize_error_message, sanitize_path

# Simple error message templates
ERROR_TEMPLATES = {
    'PROCESS_FAILED': "Process '{command}' failed with exit code {return_code}",
    'NETWORK_TIMEOUT': "Network request to '{url}' timed out after {timeout} seconds",
    'CONFIG_MISSING': "Required configuration '{key}' is missing",
    'VALIDATION_REQUIRED': "Field '{field}' is required",
    'FILE_NOT_FOUND': "File not found: {file_path}",
    'OPERATION_FAILED': "Operation '{operation}' failed: {reason}",
}


def format_error_message(template_key: str, **kwargs: Any) -> str:
    """Format an error message using a template.

    Args:
        template_key: Key for the error template
        **kwargs: Values to substitute in the template

    Returns:
        Formatted error message

    Raises:
        KeyError: If template_key is not found
        ValueError: If required template variables are missing
    """
    if template_key not in ERROR_TEMPLATES:
        raise KeyError(f"Unknown error template: {template_key}")

    template = ERROR_TEMPLATES[template_key]

    try:
        # Sanitize arguments
        sanitized_kwargs = {}
        for key, value in kwargs.items():
            if isinstance(value, str):
                if key in ('file_path', 'directory_path', 'path'):
                    sanitized_kwargs[key] = sanitize_path(value)
                else:
                    sanitized_kwargs[key] = sanitize_error_message(value)
            else:
                sanitized_kwargs[key] = value

        return template.format(**sanitized_kwargs)

    except KeyError as e:
        raise ValueError(f"Missing required template variable: {e}")


def format_process_error(
    command: str,
    return_code: Optional[int] = None,
    stderr: Optional[str] = None,
) -> str:
    """Format a process error message.

    Args:
        command: Command that failed
        return_code: Process return code
        stderr: Process stderr (will be sanitized and truncated)

    Returns:
        Formatted process error message
    """
    safe_command = sanitize_error_message(command)

    base_message = format_error_message(
        'PROCESS_FAILED',
        command=safe_command,
        return_code=return_code or 'unknown',
    )

    # Add stderr if available and informative
    if stderr and stderr.strip():
        safe_stderr = sanitize_error_message(stderr.strip())
        # Truncate long stderr
        if len(safe_stderr) > 200:
            safe_stderr = safe_stderr[:197] + "..."
        base_message += f". Error output: {safe_stderr}"

    return base_message