"""Claude-trace log analysis system for automated improvement tracking.

This system analyzes claude-trace JSON logs to identify improvements in code,
prompts, and system fixes, automatically creating GitHub issues and PRs.

Public Interface:
- TraceAnalyzer: Main orchestrator for the analysis workflow
- TraceConfig: Configuration management for the system
"""

from .config.settings import TraceConfig
from .core.orchestrator import TraceAnalyzer

__all__ = ["TraceAnalyzer", "TraceConfig"]
