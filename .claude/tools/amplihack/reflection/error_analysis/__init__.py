"""Simple error pattern detection for specific, actionable error analysis.

Provides basic error detection and concrete suggestions to replace
generic "Improve error handling based on session failures" messages.
"""

from .simple_analyzer import SimpleErrorAnalyzer

__all__ = ["SimpleErrorAnalyzer"]
