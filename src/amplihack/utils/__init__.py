"""Utility functions for amplihack."""  # noqa

from .paths import FrameworkPathResolver
from .process import ProcessManager
from .uvx_staging import stage_uvx_framework


def is_uvx_deployment() -> bool:
    """Simple UVX detection based on sys.executable location."""
    import sys

    # Check if running from UV cache (primary indicator)
    return ".cache/uv/" in sys.executable or "\\cache\\uv\\" in sys.executable


__all__ = [
    "FrameworkPathResolver",
    "ProcessManager",
    "is_uvx_deployment",
    "stage_uvx_framework",
]
