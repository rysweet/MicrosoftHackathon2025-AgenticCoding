"""Unit tests for Deduplication Engine module.

Tests multi-layer duplicate prevention for GitHub issues.
Follows TDD approach - tests written before implementation.
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from ...core.deduplication_engine import (
    ContentSimilarityChecker,
    DeduplicationEngine,
    DuplicationResult,
    ExistingIssueChecker,
    TemporalDeduplicationChecker,
)
from ...core.pattern_extractor import ImprovementPattern


class TestDeduplicationEngine(unittest.TestCase):
    """Test cases for DeduplicationEngine main orchestrator."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = DeduplicationEngine()

    def test_is_duplicate_empty_pattern(self):
        """Should handle patterns with minimal data gracefully."""
        pattern = ImprovementPattern(
            id="test-123",
            type="code_improvement",
            subtype="bug_fix",
            description="test",
            confidence=0.5,
            evidence=[],
            suggested_action="test",
        )

        result = self.engine.is_duplicate(pattern)
        self.assertIsInstance(result, DuplicationResult)
        self.assertFalse(result.is_duplicate)

    def test_is_duplicate_identical_patterns(self):
        """Should detect identical patterns as duplicates."""
        pattern1 = ImprovementPattern(
            id="test-123",
            type="code_improvement",
            subtype="bug_fix",
            description="Fixed syntax error in validation function",
            confidence=0.95,
            evidence=["before/after code"],
            suggested_action="Apply fix",
        )

        pattern2 = ImprovementPattern(
            id="test-456",
            type="code_improvement",
            subtype="bug_fix",
            description="Fixed syntax error in validation function",
            confidence=0.93,
            evidence=["test results"],
            suggested_action="Apply fix",
        )

        # First pattern should not be duplicate
        result1 = self.engine.is_duplicate(pattern1)
        self.assertFalse(result1.is_duplicate)

        # Second pattern should be detected as duplicate
        result2 = self.engine.is_duplicate(pattern2)
        self.assertTrue(result2.is_duplicate)
        self.assertEqual(result2.duplication_type, "content_similarity")

    def test_is_duplicate_similar_descriptions(self):
        """Should detect patterns with similar descriptions."""
        pattern1 = ImprovementPattern(
            id="test-123",
            type="code_improvement",
            subtype="performance",
            description="Optimized database query performance using indexing",
            confidence=0.9,
            evidence=["performance metrics"],
            suggested_action="Apply optimization",
        )

        pattern2 = ImprovementPattern(
            id="test-456",
            type="code_improvement",
            subtype="performance",
            description="Improved database query performance with proper indexing",
            confidence=0.85,
            evidence=["benchmark results"],
            suggested_action="Review optimization",
        )

        # First pattern
        result1 = self.engine.is_duplicate(pattern1)
        self.assertFalse(result1.is_duplicate)

        # Second pattern should be similar enough to be considered duplicate
        result2 = self.engine.is_duplicate(pattern2)
        self.assertTrue(result2.is_duplicate)
        self.assertIn("similarity", result2.duplication_type)

    def test_is_duplicate_temporal_filtering(self):
        """Should detect patterns that are too close in time."""
        base_time = datetime.now()

        # Create patterns with timestamps close together
        pattern1 = ImprovementPattern(
            id="test-123",
            type="prompt_improvement",
            subtype="clarity",
            description="Improved prompt clarity for API requests",
            confidence=0.8,
            evidence=["user feedback"],
            suggested_action="Update templates",
            metadata={"timestamp": base_time.isoformat()},
        )

        pattern2 = ImprovementPattern(
            id="test-456",
            type="prompt_improvement",
            subtype="clarity",
            description="Enhanced prompt clarity for API calls",
            confidence=0.75,
            evidence=["analysis results"],
            suggested_action="Revise templates",
            metadata={"timestamp": (base_time + timedelta(minutes=5)).isoformat()},
        )

        # First pattern
        result1 = self.engine.is_duplicate(pattern1)
        self.assertFalse(result1.is_duplicate)

        # Second pattern should be detected as temporal duplicate
        result2 = self.engine.is_duplicate(pattern2)
        self.assertTrue(result2.is_duplicate)
        self.assertEqual(result2.duplication_type, "temporal")

    def test_is_duplicate_different_types_not_duplicate(self):
        """Should not consider patterns of different types as duplicates."""
        pattern1 = ImprovementPattern(
            id="test-123",
            type="code_improvement",
            subtype="bug_fix",
            description="Fixed validation error",
            confidence=0.9,
            evidence=["test results"],
            suggested_action="Apply fix",
        )

        pattern2 = ImprovementPattern(
            id="test-456",
            type="system_fix",
            subtype="connection",
            description="Fixed validation error",
            confidence=0.85,
            evidence=["error logs"],
            suggested_action="Apply fix",
        )

        # Different types should not be considered duplicates
        result1 = self.engine.is_duplicate(pattern1)
        self.assertFalse(result1.is_duplicate)

        result2 = self.engine.is_duplicate(pattern2)
        self.assertFalse(result2.is_duplicate)

    def test_get_deduplication_report(self):
        """Should provide comprehensive deduplication report."""
        pattern = ImprovementPattern(
            id="test-123",
            type="code_improvement",
            subtype="bug_fix",
            description="test pattern",
            confidence=0.8,
            evidence=[],
            suggested_action="test",
        )

        # Process pattern to generate report data
        self.engine.is_duplicate(pattern)

        report = self.engine.get_deduplication_report()
        self.assertIsInstance(report, dict)
        self.assertIn("total_patterns_checked", report)
        self.assertIn("duplicates_found", report)
        self.assertIn("unique_patterns", report)
        self.assertIn("duplication_types", report)

    def test_reset_cache(self):
        """Should reset internal caches and state."""
        pattern = ImprovementPattern(
            id="test-123",
            type="code_improvement",
            subtype="bug_fix",
            description="test pattern",
            confidence=0.8,
            evidence=[],
            suggested_action="test",
        )

        # Process pattern
        self.engine.is_duplicate(pattern)

        # Reset and verify cache is cleared
        self.engine.reset_cache()

        # Pattern should not be considered duplicate after reset
        result = self.engine.is_duplicate(pattern)
        self.assertFalse(result.is_duplicate)


class TestContentSimilarityChecker(unittest.TestCase):
    """Test cases for ContentSimilarityChecker."""

    def setUp(self):
        """Set up test fixtures."""
        self.checker = ContentSimilarityChecker()

    def test_check_identical_descriptions(self):
        """Should detect identical descriptions as duplicates."""
        pattern1 = self._create_pattern("Fixed bug in authentication module")
        pattern2 = self._create_pattern("Fixed bug in authentication module")

        # First pattern
        result1 = self.checker.check_duplication(pattern1, [])
        self.assertFalse(result1.is_duplicate)

        # Second pattern should be duplicate
        result2 = self.checker.check_duplication(pattern2, [pattern1])
        self.assertTrue(result2.is_duplicate)

    def test_check_similar_descriptions(self):
        """Should detect similar descriptions based on similarity threshold."""
        pattern1 = self._create_pattern("Fixed authentication bug in user login")
        pattern2 = self._create_pattern("Resolved authentication issue in user login")

        result1 = self.checker.check_duplication(pattern1, [])
        self.assertFalse(result1.is_duplicate)

        result2 = self.checker.check_duplication(pattern2, [pattern1])
        self.assertTrue(result2.is_duplicate)

    def test_check_different_descriptions(self):
        """Should not detect completely different descriptions as duplicates."""
        pattern1 = self._create_pattern("Fixed authentication bug")
        pattern2 = self._create_pattern("Optimized database performance")

        result1 = self.checker.check_duplication(pattern1, [])
        self.assertFalse(result1.is_duplicate)

        result2 = self.checker.check_duplication(pattern2, [pattern1])
        self.assertFalse(result2.is_duplicate)

    def test_similarity_threshold_configuration(self):
        """Should respect configurable similarity threshold."""
        # Test with high threshold (less sensitive)
        high_threshold_checker = ContentSimilarityChecker(similarity_threshold=0.9)

        pattern1 = self._create_pattern("Fixed bug in login system")
        pattern2 = self._create_pattern("Resolved issue in login system")

        result1 = high_threshold_checker.check_duplication(pattern1, [])
        self.assertFalse(result1.is_duplicate)

        result2 = high_threshold_checker.check_duplication(pattern2, [pattern1])
        # With high threshold, should not be considered duplicate
        self.assertFalse(result2.is_duplicate)

    def test_check_with_multiple_existing_patterns(self):
        """Should check against multiple existing patterns."""
        existing_patterns = [
            self._create_pattern("Fixed database connection issue"),
            self._create_pattern("Improved API response time"),
            self._create_pattern("Added input validation"),
        ]

        new_pattern = self._create_pattern("Resolved database connection problem")

        result = self.checker.check_duplication(new_pattern, existing_patterns)
        self.assertTrue(result.is_duplicate)

    def _create_pattern(self, description: str) -> ImprovementPattern:
        """Helper to create test patterns."""
        return ImprovementPattern(
            id=f"test-{hash(description)}",
            type="code_improvement",
            subtype="bug_fix",
            description=description,
            confidence=0.8,
            evidence=[],
            suggested_action="test action",
        )


class TestTemporalDeduplicationChecker(unittest.TestCase):
    """Test cases for TemporalDeduplicationChecker."""

    def setUp(self):
        """Set up test fixtures."""
        self.checker = TemporalDeduplicationChecker()

    def test_check_patterns_close_in_time(self):
        """Should detect patterns that are too close in time."""
        base_time = datetime.now()

        pattern1 = self._create_pattern_with_time("Fixed login bug", base_time)

        pattern2 = self._create_pattern_with_time(
            "Resolved login issue",  # Similar but different
            base_time + timedelta(minutes=5),  # Within time window
        )

        result1 = self.checker.check_duplication(pattern1, [])
        self.assertFalse(result1.is_duplicate)

        result2 = self.checker.check_duplication(pattern2, [pattern1])
        self.assertTrue(result2.is_duplicate)
        self.assertEqual(result2.duplication_type, "temporal")

    def test_check_patterns_far_in_time(self):
        """Should not detect patterns that are far apart in time."""
        base_time = datetime.now()

        pattern1 = self._create_pattern_with_time("Fixed login bug", base_time)

        pattern2 = self._create_pattern_with_time(
            "Resolved login issue",
            base_time + timedelta(hours=2),  # Outside time window
        )

        result1 = self.checker.check_duplication(pattern1, [])
        self.assertFalse(result1.is_duplicate)

        result2 = self.checker.check_duplication(pattern2, [pattern1])
        self.assertFalse(result2.is_duplicate)

    def test_check_different_types_ignore_temporal(self):
        """Should not apply temporal deduplication to different pattern types."""
        base_time = datetime.now()

        pattern1 = ImprovementPattern(
            id="test-1",
            type="code_improvement",
            subtype="bug_fix",
            description="Fixed issue",
            confidence=0.8,
            evidence=[],
            suggested_action="test",
            metadata={"timestamp": base_time.isoformat()},
        )

        pattern2 = ImprovementPattern(
            id="test-2",
            type="system_fix",  # Different type
            subtype="connection",
            description="Fixed issue",
            confidence=0.8,
            evidence=[],
            suggested_action="test",
            metadata={"timestamp": (base_time + timedelta(minutes=5)).isoformat()},
        )

        result1 = self.checker.check_duplication(pattern1, [])
        self.assertFalse(result1.is_duplicate)

        result2 = self.checker.check_duplication(pattern2, [pattern1])
        self.assertFalse(result2.is_duplicate)

    def test_configurable_time_window(self):
        """Should respect configurable time window."""
        # Short time window (30 minutes)
        short_window_checker = TemporalDeduplicationChecker(time_window_minutes=30)

        base_time = datetime.now()
        pattern1 = self._create_pattern_with_time("Fixed bug", base_time)
        pattern2 = self._create_pattern_with_time(
            "Resolved bug",
            base_time + timedelta(minutes=45),  # Outside 30-minute window
        )

        result1 = short_window_checker.check_duplication(pattern1, [])
        self.assertFalse(result1.is_duplicate)

        result2 = short_window_checker.check_duplication(pattern2, [pattern1])
        self.assertFalse(result2.is_duplicate)

    def _create_pattern_with_time(
        self, description: str, timestamp: datetime
    ) -> ImprovementPattern:
        """Helper to create patterns with specific timestamps."""
        return ImprovementPattern(
            id=f"test-{hash(description + str(timestamp))}",
            type="code_improvement",
            subtype="bug_fix",
            description=description,
            confidence=0.8,
            evidence=[],
            suggested_action="test",
            metadata={"timestamp": timestamp.isoformat()},
        )


class TestExistingIssueChecker(unittest.TestCase):
    """Test cases for ExistingIssueChecker."""

    def setUp(self):
        """Set up test fixtures."""
        self.checker = ExistingIssueChecker()

    @patch("requests.get")
    def test_check_no_existing_issues(self, mock_get):
        """Should not find duplicates when no existing issues match."""
        # Mock GitHub API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        pattern = self._create_test_pattern("New unique improvement")

        result = self.checker.check_duplication(pattern, [])
        self.assertFalse(result.is_duplicate)

    @patch("requests.get")
    def test_check_existing_similar_issue(self, mock_get):
        """Should detect existing GitHub issues with similar titles."""
        # Mock GitHub API response with similar issue
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "title": "Fixed authentication bug in login system",
                "body": "Description of the fix",
                "number": 123,
                "state": "open",
            }
        ]
        mock_get.return_value = mock_response

        pattern = self._create_test_pattern("Resolved authentication issue in login")

        result = self.checker.check_duplication(pattern, [])
        self.assertTrue(result.is_duplicate)
        self.assertEqual(result.duplication_type, "existing_issue")
        self.assertIn("123", result.reason)

    @patch("requests.get")
    def test_check_api_error_handling(self, mock_get):
        """Should handle GitHub API errors gracefully."""
        # Mock API error
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.raise_for_status.side_effect = Exception("API Error")
        mock_get.return_value = mock_response

        pattern = self._create_test_pattern("Test pattern")

        # Should not crash and should not consider as duplicate
        result = self.checker.check_duplication(pattern, [])
        self.assertFalse(result.is_duplicate)

    @patch("requests.get")
    def test_check_rate_limiting(self, mock_get):
        """Should handle rate limiting appropriately."""
        # Mock rate limit response
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response

        pattern = self._create_test_pattern("Test pattern")

        result = self.checker.check_duplication(pattern, [])
        # Should be conservative and not consider as duplicate when rate limited
        self.assertFalse(result.is_duplicate)

    def _create_test_pattern(self, description: str) -> ImprovementPattern:
        """Helper to create test patterns."""
        return ImprovementPattern(
            id=f"test-{hash(description)}",
            type="code_improvement",
            subtype="bug_fix",
            description=description,
            confidence=0.8,
            evidence=[],
            suggested_action="test action",
        )


class TestDuplicationResult(unittest.TestCase):
    """Test cases for DuplicationResult data model."""

    def test_result_creation_not_duplicate(self):
        """Should create result indicating no duplication."""
        result = DuplicationResult(
            is_duplicate=False,
            duplication_type="none",
            reason="No similar patterns found",
            confidence=0.0,
        )

        self.assertFalse(result.is_duplicate)
        self.assertEqual(result.duplication_type, "none")
        self.assertEqual(result.confidence, 0.0)

    def test_result_creation_duplicate(self):
        """Should create result indicating duplication found."""
        result = DuplicationResult(
            is_duplicate=True,
            duplication_type="content_similarity",
            reason="Similar description found",
            confidence=0.95,
        )

        self.assertTrue(result.is_duplicate)
        self.assertEqual(result.duplication_type, "content_similarity")
        self.assertEqual(result.confidence, 0.95)

    def test_result_validation(self):
        """Should validate result fields."""
        with self.assertRaises(ValueError):
            DuplicationResult(
                is_duplicate=True,
                duplication_type="",  # Empty type should fail
                reason="test",
                confidence=0.5,
            )

        with self.assertRaises(ValueError):
            DuplicationResult(
                is_duplicate=True,
                duplication_type="test",
                reason="test",
                confidence=1.5,  # Invalid confidence
            )

    def test_result_to_dict(self):
        """Should convert result to dictionary representation."""
        result = DuplicationResult(
            is_duplicate=True,
            duplication_type="temporal",
            reason="Pattern found within time window",
            confidence=0.8,
        )

        result_dict = result.to_dict()
        self.assertEqual(result_dict["is_duplicate"], True)
        self.assertEqual(result_dict["duplication_type"], "temporal")
        self.assertEqual(result_dict["confidence"], 0.8)


if __name__ == "__main__":
    unittest.main()
