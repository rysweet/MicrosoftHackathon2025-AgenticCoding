"""Simple error analyzer that provides specific, actionable error analysis."""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional

try:
    from ..security import filter_pattern_suggestion, sanitize_content
except ImportError:
    # Fallback for testing
    def sanitize_content(content: str, max_length: int = 500) -> str:
        return content[:max_length] + "..." if len(content) > max_length else content

    def filter_pattern_suggestion(suggestion: str) -> str:
        return suggestion[:100] + "..." if len(suggestion) > 100 else suggestion


@dataclass
class ErrorPattern:
    """Represents a detected error pattern with specific suggestion."""

    error_type: str
    priority: str  # "high", "medium", "low"
    suggestion: str
    confidence: float


class SimpleErrorAnalyzer:
    """Simple error analyzer that provides specific, actionable suggestions."""

    def __init__(self):
        # Pre-compiled priority mapping for performance
        self._priority_order = {"high": 3, "medium": 2, "low": 1}

        # Simple LRU cache for repeated content (limited size for memory efficiency)
        self._content_cache = {}
        self._cache_size_limit = 10
        # Essential error patterns with specific suggestions
        self.error_patterns = [
            # File system errors
            (
                r"(?i)(filenotfounderror|no such file|file.*not found)",
                "file_missing",
                "high",
                "Add file existence checks before operations",
            ),
            (
                r"(?i)(permissionerror|permission denied)",
                "file_permissions",
                "high",
                "Fix file/directory permissions or run with proper access",
            ),
            # API/Network errors
            (
                r"(?i)(http.*error|api.*error|connection.*error)",
                "api_failure",
                "medium",
                "Add retry logic and proper error handling for API calls",
            ),
            (
                r"(?i)(timeout|timed out)",
                "timeout_error",
                "medium",
                "Increase timeout values or implement retry with exponential backoff",
            ),
            # Python specific errors
            (
                r"(?i)(modulenotfounderror|no module named)",
                "missing_dependency",
                "high",
                "Install missing Python package or fix import path",
            ),
            (
                r"(?i)(syntaxerror|invalid syntax)",
                "syntax_error",
                "high",
                "Fix syntax errors using IDE or linter",
            ),
            (r"(?i)(typeerror)", "type_error", "medium", "Add type checking and validation"),
            # Runtime errors
            (
                r"(?i)(indexerror|list index out of range)",
                "index_error",
                "medium",
                "Add bounds checking before accessing list elements",
            ),
            (
                r"(?i)(keyerror)",
                "key_error",
                "medium",
                "Check key existence before dictionary access",
            ),
            # General failures
            (
                r"(?i)(failed|failure)",
                "general_failure",
                "low",
                "Add specific error handling and logging for failed operations",
            ),
        ]

        # Compile patterns for performance with optimized flags
        # Sort patterns by priority for faster early detection
        sorted_patterns = sorted(
            self.error_patterns, key=lambda x: self._priority_order.get(x[2], 0), reverse=True
        )

        self.compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), error_type, priority, suggestion)
            for pattern, error_type, priority, suggestion in sorted_patterns
        ]

    def analyze_errors(self, content: str) -> List[ErrorPattern]:
        """Analyze content for error patterns and return specific suggestions.

        Args:
            content: Session content to analyze

        Returns:
            List of ErrorPattern objects with specific suggestions
        """
        # Early exit for empty or very short content
        if not content or len(content.strip()) < 10:
            return []

        # Check cache first (using content hash for memory efficiency)
        content_hash = hash(content) % 1000000  # Simple hash for caching
        if content_hash in self._content_cache:
            return self._content_cache[content_hash]

        # Sanitize content for security
        safe_content = sanitize_content(content, max_length=5000)

        # Early exit if sanitized content is too short
        if len(safe_content.strip()) < 10:
            return []

        detected_patterns = []
        seen_types = set()

        # Check each pattern
        for pattern, error_type, priority, suggestion in self.compiled_patterns:
            if error_type in seen_types:
                continue

            match = pattern.search(safe_content)
            if match:
                # Optimized confidence calculation - avoid findall() for performance
                # Use a simple heuristic based on match position and pattern complexity
                match_pos = match.start() / len(safe_content) if safe_content else 0
                confidence = min(0.95, 0.7 + (0.25 * (1 - match_pos)))

                # Apply security filtering
                safe_suggestion = filter_pattern_suggestion(suggestion)

                error_pattern = ErrorPattern(
                    error_type=error_type,
                    priority=priority,
                    suggestion=safe_suggestion,
                    confidence=confidence,
                )
                detected_patterns.append(error_pattern)
                seen_types.add(error_type)

                # Early exit if we have enough high-priority patterns
                if len(detected_patterns) >= 5 and priority == "high":
                    break

        # Sort by priority and confidence (using pre-compiled mapping)
        detected_patterns.sort(
            key=lambda p: (self._priority_order.get(p.priority, 0), p.confidence), reverse=True
        )

        result = detected_patterns[:3]  # Return top 3 patterns

        # Cache result (with size limit to prevent memory bloat)
        if len(self._content_cache) >= self._cache_size_limit:
            # Remove oldest entry
            oldest_key = next(iter(self._content_cache))
            del self._content_cache[oldest_key]

        self._content_cache[content_hash] = result
        return result

    def get_top_suggestion(self, content: str) -> Optional[Dict]:
        """Get the top error suggestion for the reflection system.

        Args:
            content: Session content to analyze

        Returns:
            Dictionary with suggestion details or None
        """
        patterns = self.analyze_errors(content)

        if not patterns:
            return None

        top_pattern = patterns[0]
        return {
            "type": f"error_{top_pattern.error_type}",
            "priority": top_pattern.priority,
            "suggestion": top_pattern.suggestion,
            "confidence": top_pattern.confidence,
            "implementation_steps": self._get_implementation_steps(top_pattern.error_type),
        }

    def _get_implementation_steps(self, error_type: str) -> List[str]:
        """Get simple implementation steps for error type."""
        steps_map = {
            "file_missing": [
                "Use pathlib.Path.exists() or os.path.exists() before file operations",
                "Add try-catch blocks around file operations",
            ],
            "file_permissions": [
                "Check file permissions with os.access()",
                "Use appropriate file modes when opening files",
            ],
            "api_failure": [
                "Add try-catch for requests.exceptions",
                "Implement retry logic with exponential backoff",
            ],
            "timeout_error": [
                "Increase timeout parameters in requests/network calls",
                "Add connection pooling for better reliability",
            ],
            "missing_dependency": [
                "Add missing package to requirements.txt",
                "Install package with pip install <package>",
            ],
            "syntax_error": [
                "Run code through linter (flake8, pylint)",
                "Use IDE with syntax highlighting and error detection",
            ],
            "type_error": [
                "Add type hints to function parameters",
                "Validate input types before processing",
            ],
            "index_error": [
                "Check list length before accessing elements",
                "Use try-catch or conditional checks",
            ],
            "key_error": [
                "Use dict.get() with default values",
                "Check key existence with 'key in dict'",
            ],
        }
        return steps_map.get(error_type, ["Add error handling and logging"])
