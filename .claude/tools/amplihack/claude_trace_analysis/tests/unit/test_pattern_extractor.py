"""Unit tests for Pattern Extractor module.

Tests specialized analyzers for identifying improvement patterns.
Follows TDD approach - tests written before implementation.
"""

import unittest

from ...core.jsonl_parser import ParsedEntry
from ...core.pattern_extractor import (
    CodeImprovementAnalyzer,
    ImprovementPattern,
    PatternExtractor,
    PromptImprovementAnalyzer,
    SystemFixAnalyzer,
)


class TestPatternExtractor(unittest.TestCase):
    """Test cases for PatternExtractor main orchestrator."""

    def setUp(self):
        """Set up test fixtures."""
        self.extractor = PatternExtractor()

    def test_extract_patterns_empty_entries(self):
        """Should handle empty entry list gracefully."""
        patterns = self.extractor.extract_patterns([])
        self.assertEqual(len(patterns), 0)

    def test_extract_patterns_no_improvements(self):
        """Should return empty list when no improvements detected."""
        entries = [
            ParsedEntry(
                timestamp="2024-01-01T12:00:00",
                entry_type="completion",
                data={"prompt": "simple request", "completion": "simple response"},
            )
        ]

        patterns = self.extractor.extract_patterns(entries)
        self.assertEqual(len(patterns), 0)

    def test_extract_code_improvement_patterns(self):
        """Should identify code improvement patterns."""
        entries = [
            ParsedEntry(
                timestamp="2024-01-01T12:00:00",
                entry_type="completion",
                data={
                    "prompt": "Fix the bug in this function",
                    "completion": "Here's the fixed function with proper error handling",
                    "code_before": "def broken_func(): pass",
                    "code_after": "def fixed_func(): try: pass except: handle_error()",
                },
            )
        ]

        patterns = self.extractor.extract_patterns(entries)
        self.assertGreater(len(patterns), 0)
        self.assertEqual(patterns[0]["type"], "code_improvement")

    def test_extract_prompt_improvement_patterns(self):
        """Should identify prompt improvement patterns."""
        entries = [
            ParsedEntry(
                timestamp="2024-01-01T12:00:00",
                entry_type="completion",
                data={
                    "prompt": "unclear request",
                    "completion": "I need more specific details to help you properly",
                    "follow_up_prompt": "Here's a more detailed request with context",
                },
            )
        ]

        patterns = self.extractor.extract_patterns(entries)
        self.assertGreater(len(patterns), 0)
        self.assertEqual(patterns[0]["type"], "prompt_improvement")

    def test_extract_system_fix_patterns(self):
        """Should identify system fix patterns."""
        entries = [
            ParsedEntry(
                timestamp="2024-01-01T12:00:00",
                entry_type="error",
                data={
                    "error": "Connection timeout",
                    "resolution": "Added retry logic with exponential backoff",
                    "fix_applied": True,
                },
            )
        ]

        patterns = self.extractor.extract_patterns(entries)
        self.assertGreater(len(patterns), 0)
        self.assertEqual(patterns[0]["type"], "system_fix")

    def test_extract_patterns_multiple_types(self):
        """Should identify multiple pattern types in mixed entries."""
        entries = [
            ParsedEntry(
                timestamp="2024-01-01T12:00:00",
                entry_type="completion",
                data={
                    "prompt": "Fix the bug",
                    "completion": "Fixed with better error handling",
                    "code_improvement": True,
                },
            ),
            ParsedEntry(
                timestamp="2024-01-01T12:01:00",
                entry_type="completion",
                data={
                    "prompt": "vague request",
                    "completion": "Could you be more specific?",
                    "clarification_needed": True,
                },
            ),
        ]

        patterns = self.extractor.extract_patterns(entries)
        self.assertGreaterEqual(len(patterns), 2)
        pattern_types = [p["type"] for p in patterns]
        self.assertIn("code_improvement", pattern_types)
        self.assertIn("prompt_improvement", pattern_types)

    def test_pattern_deduplication_within_extractor(self):
        """Should avoid extracting duplicate patterns."""
        # Same improvement identified multiple times
        entries = [
            ParsedEntry(
                timestamp="2024-01-01T12:00:00",
                entry_type="completion",
                data={"improvement": "add error handling", "context": "function A"},
            ),
            ParsedEntry(
                timestamp="2024-01-01T12:01:00",
                entry_type="completion",
                data={"improvement": "add error handling", "context": "function A"},
            ),
        ]

        patterns = self.extractor.extract_patterns(entries)
        # Should be deduplicated to 1 pattern
        self.assertLessEqual(len(patterns), 1)


class TestCodeImprovementAnalyzer(unittest.TestCase):
    """Test cases for CodeImprovementAnalyzer."""

    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = CodeImprovementAnalyzer()

    def test_analyze_no_code_improvements(self):
        """Should return empty list when no code improvements found."""
        entries = [
            ParsedEntry(
                timestamp="2024-01-01T12:00:00",
                entry_type="completion",
                data={"prompt": "what is python", "completion": "Python is a language"},
            )
        ]

        patterns = self.analyzer.analyze(entries)
        self.assertEqual(len(patterns), 0)

    def test_analyze_bug_fix_pattern(self):
        """Should identify bug fix patterns."""
        entries = [
            ParsedEntry(
                timestamp="2024-01-01T12:00:00",
                entry_type="completion",
                data={
                    "prompt": "This function has a bug",
                    "completion": "Here's the fixed version",
                    "code_change": {
                        "before": "if x = 5:",
                        "after": "if x == 5:",
                        "type": "syntax_fix",
                    },
                },
            )
        ]

        patterns = self.analyzer.analyze(entries)
        self.assertEqual(len(patterns), 1)
        pattern = patterns[0]
        self.assertEqual(pattern.type, "code_improvement")
        self.assertEqual(pattern.subtype, "bug_fix")
        self.assertIn("syntax_fix", pattern.description)

    def test_analyze_performance_improvement(self):
        """Should identify performance improvement patterns."""
        entries = [
            ParsedEntry(
                timestamp="2024-01-01T12:00:00",
                entry_type="completion",
                data={
                    "prompt": "Optimize this slow function",
                    "completion": "Here's the optimized version using caching",
                    "performance_gain": "50x faster",
                    "optimization_type": "caching",
                },
            )
        ]

        patterns = self.analyzer.analyze(entries)
        self.assertEqual(len(patterns), 1)
        pattern = patterns[0]
        self.assertEqual(pattern.subtype, "performance")
        self.assertIn("caching", pattern.description)

    def test_analyze_security_improvement(self):
        """Should identify security improvement patterns."""
        entries = [
            ParsedEntry(
                timestamp="2024-01-01T12:00:00",
                entry_type="completion",
                data={
                    "prompt": "This code has a security vulnerability",
                    "completion": "Fixed SQL injection with prepared statements",
                    "security_fix": True,
                    "vulnerability_type": "sql_injection",
                },
            )
        ]

        patterns = self.analyzer.analyze(entries)
        self.assertEqual(len(patterns), 1)
        pattern = patterns[0]
        self.assertEqual(pattern.subtype, "security")
        self.assertIn("sql_injection", pattern.description)


class TestPromptImprovementAnalyzer(unittest.TestCase):
    """Test cases for PromptImprovementAnalyzer."""

    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = PromptImprovementAnalyzer()

    def test_analyze_clarity_improvement(self):
        """Should identify prompt clarity improvements."""
        entries = [
            ParsedEntry(
                timestamp="2024-01-01T12:00:00",
                entry_type="completion",
                data={
                    "prompt": "do something",
                    "completion": "I need more specific details",
                    "clarification_request": True,
                    "improved_prompt": "Create a Python function that validates email addresses",
                },
            )
        ]

        patterns = self.analyzer.analyze(entries)
        self.assertEqual(len(patterns), 1)
        pattern = patterns[0]
        self.assertEqual(pattern.type, "prompt_improvement")
        self.assertEqual(pattern.subtype, "clarity")

    def test_analyze_context_improvement(self):
        """Should identify context improvement patterns."""
        entries = [
            ParsedEntry(
                timestamp="2024-01-01T12:00:00",
                entry_type="completion",
                data={
                    "prompt": "fix this",
                    "completion": "I need to see the code to help",
                    "context_missing": True,
                    "improved_prompt": "fix this Python function: def broken(): ...",
                },
            )
        ]

        patterns = self.analyzer.analyze(entries)
        self.assertEqual(len(patterns), 1)
        pattern = patterns[0]
        self.assertEqual(pattern.subtype, "context")

    def test_analyze_specificity_improvement(self):
        """Should identify specificity improvement patterns."""
        entries = [
            ParsedEntry(
                timestamp="2024-01-01T12:00:00",
                entry_type="completion",
                data={
                    "prompt": "make it better",
                    "completion": "What specific improvements do you want?",
                    "specificity_needed": True,
                    "improved_prompt": "improve performance by 50% using caching",
                },
            )
        ]

        patterns = self.analyzer.analyze(entries)
        self.assertEqual(len(patterns), 1)
        pattern = patterns[0]
        self.assertEqual(pattern.subtype, "specificity")


class TestSystemFixAnalyzer(unittest.TestCase):
    """Test cases for SystemFixAnalyzer."""

    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = SystemFixAnalyzer()

    def test_analyze_connection_fix(self):
        """Should identify connection fix patterns."""
        entries = [
            ParsedEntry(
                timestamp="2024-01-01T12:00:00",
                entry_type="error",
                data={
                    "error_type": "connection_timeout",
                    "error_message": "Connection timed out after 30 seconds",
                    "fix_applied": "Added retry logic with exponential backoff",
                    "success": True,
                },
            )
        ]

        patterns = self.analyzer.analyze(entries)
        self.assertEqual(len(patterns), 1)
        pattern = patterns[0]
        self.assertEqual(pattern.type, "system_fix")
        self.assertEqual(pattern.subtype, "connection")

    def test_analyze_memory_fix(self):
        """Should identify memory-related fix patterns."""
        entries = [
            ParsedEntry(
                timestamp="2024-01-01T12:00:00",
                entry_type="error",
                data={
                    "error_type": "out_of_memory",
                    "error_message": "Process exceeded memory limit",
                    "fix_applied": "Implemented streaming for large datasets",
                    "memory_usage_reduced": "75%",
                },
            )
        ]

        patterns = self.analyzer.analyze(entries)
        self.assertEqual(len(patterns), 1)
        pattern = patterns[0]
        self.assertEqual(pattern.subtype, "memory")

    def test_analyze_api_fix(self):
        """Should identify API-related fix patterns."""
        entries = [
            ParsedEntry(
                timestamp="2024-01-01T12:00:00",
                entry_type="error",
                data={
                    "error_type": "api_rate_limit",
                    "error_message": "API rate limit exceeded",
                    "fix_applied": "Added rate limiting with backoff strategy",
                    "api_stability_improved": True,
                },
            )
        ]

        patterns = self.analyzer.analyze(entries)
        self.assertEqual(len(patterns), 1)
        pattern = patterns[0]
        self.assertEqual(pattern.subtype, "api")


class TestImprovementPattern(unittest.TestCase):
    """Test cases for ImprovementPattern data model."""

    def test_pattern_creation(self):
        """Should create ImprovementPattern with required fields."""
        pattern = ImprovementPattern(
            id="test-123",
            type="code_improvement",
            subtype="bug_fix",
            description="Fixed syntax error in validation function",
            confidence=0.95,
            evidence=["before/after code", "test results"],
            suggested_action="Review and apply fix to similar patterns",
        )

        self.assertEqual(pattern.id, "test-123")
        self.assertEqual(pattern.type, "code_improvement")
        self.assertEqual(pattern.confidence, 0.95)
        self.assertIn("before/after code", pattern.evidence)

    def test_pattern_validation(self):
        """Should validate ImprovementPattern fields."""
        with self.assertRaises(ValueError):
            ImprovementPattern(
                id="",  # Empty ID should fail
                type="code_improvement",
                subtype="bug_fix",
                description="test",
                confidence=0.95,
                evidence=[],
                suggested_action="test",
            )

        with self.assertRaises(ValueError):
            ImprovementPattern(
                id="test-123",
                type="code_improvement",
                subtype="bug_fix",
                description="test",
                confidence=1.5,  # Invalid confidence (>1.0)
                evidence=[],
                suggested_action="test",
            )

    def test_pattern_to_dict(self):
        """Should convert pattern to dictionary representation."""
        pattern = ImprovementPattern(
            id="test-123",
            type="code_improvement",
            subtype="bug_fix",
            description="test description",
            confidence=0.95,
            evidence=["evidence1"],
            suggested_action="test action",
        )

        pattern_dict = pattern.to_dict()
        self.assertEqual(pattern_dict["id"], "test-123")
        self.assertEqual(pattern_dict["type"], "code_improvement")
        self.assertEqual(pattern_dict["confidence"], 0.95)


if __name__ == "__main__":
    unittest.main()
