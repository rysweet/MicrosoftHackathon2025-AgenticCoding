"""Unit tests for TraceAnalyzer orchestrator module.

Tests the main workflow orchestrator for claude-trace analysis system.
Follows TDD approach with comprehensive coverage of all components.
"""

import tempfile
import unittest
from pathlib import Path
from typing import List, cast
from unittest.mock import MagicMock, Mock, patch

from ...core.issue_generator import IssueCreationResult
from ...core.jsonl_parser import ParsedEntry, ValidationError
from ...core.orchestrator import AnalysisResult, TraceAnalyzer
from ...core.pattern_extractor import ImprovementPattern


class TestAnalysisResult(unittest.TestCase):
    """Test cases for AnalysisResult data class."""

    def test_analysis_result_creation(self):
        """Should create AnalysisResult with required fields."""
        result = AnalysisResult(success=True)

        self.assertTrue(result.success)
        self.assertEqual(result.files_processed, 0)
        self.assertEqual(result.entries_parsed, 0)
        self.assertEqual(result.patterns_identified, 0)
        self.assertEqual(result.unique_patterns, 0)
        self.assertEqual(result.issues_created, 0)
        self.assertEqual(result.execution_time_seconds, 0.0)
        self.assertIsNone(result.error_message)
        self.assertEqual(result.detailed_results, {})

    def test_analysis_result_to_dict(self):
        """Should convert AnalysisResult to dictionary correctly."""
        result = AnalysisResult(
            success=True,
            files_processed=2,
            entries_parsed=10,
            patterns_identified=5,
            unique_patterns=3,
            issues_created=2,
            execution_time_seconds=1.5,
            detailed_results={"test": "data"},
        )

        result_dict = result.to_dict()

        self.assertTrue(result_dict["success"])
        self.assertEqual(result_dict["summary"]["files_processed"], 2)
        self.assertEqual(result_dict["summary"]["entries_parsed"], 10)
        self.assertEqual(result_dict["summary"]["patterns_identified"], 5)
        self.assertEqual(result_dict["summary"]["unique_patterns"], 3)
        self.assertEqual(result_dict["summary"]["issues_created"], 2)
        self.assertEqual(result_dict["summary"]["execution_time_seconds"], 1.5)
        self.assertIsNone(result_dict["error_message"])
        self.assertEqual(result_dict["detailed_results"], {"test": "data"})


class TestTraceAnalyzer(unittest.TestCase):
    """Test cases for TraceAnalyzer main orchestrator."""

    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = TraceAnalyzer()

        # Mock components with proper typing
        self.analyzer.parser = cast(Mock, MagicMock())
        self.analyzer.pattern_extractor = cast(Mock, MagicMock())
        self.analyzer.deduplication_engine = cast(Mock, MagicMock())
        self.analyzer.issue_generator = cast(Mock, MagicMock())

    def test_init_with_defaults(self):
        """Should initialize with default configuration."""
        analyzer = TraceAnalyzer()

        self.assertFalse(analyzer.github_integration_enabled)
        self.assertIsNone(analyzer.last_analysis_result)
        self.assertIsNotNone(analyzer.parser)
        self.assertIsNotNone(analyzer.pattern_extractor)
        self.assertIsNotNone(analyzer.deduplication_engine)
        self.assertIsNotNone(analyzer.issue_generator)

    def test_init_with_github_config(self):
        """Should initialize with GitHub integration enabled."""
        analyzer = TraceAnalyzer(
            github_token="test_token", repo_owner="test_owner", repo_name="test_repo"
        )

        self.assertTrue(analyzer.github_integration_enabled)

    def test_analyze_trace_files_no_entries(self):
        """Should handle case when no entries are parsed."""
        self.analyzer.parser.parse_file.return_value = []  # type: ignore

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write('{"test": "data"}\n')
            file_path = f.name

        try:
            result = self.analyzer.analyze_trace_files([file_path])

            self.assertFalse(result.success)
            self.assertIsNotNone(result.error_message)
            error_msg = result.error_message
            assert error_msg is not None  # Type narrowing for pyright
            self.assertIn("No valid entries found", error_msg)
            self.assertEqual(result.files_processed, 0)
            self.assertEqual(result.entries_parsed, 0)
        finally:
            Path(file_path).unlink()

    def test_analyze_trace_files_success_no_patterns(self):
        """Should handle successful parse with no patterns."""
        # Mock components
        mock_entries = [
            ParsedEntry(
                timestamp="2024-01-01T12:00:00",
                entry_type="completion",
                data={"prompt": "test", "completion": "response"},
            )
        ]
        self.analyzer.parser.parse_file.return_value = mock_entries  # type: ignore
        self.analyzer.pattern_extractor.extract_patterns.return_value = []  # type: ignore

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write('{"test": "data"}\n')
            file_path = f.name

        try:
            result = self.analyzer.analyze_trace_files([file_path])

            self.assertTrue(result.success)
            self.assertEqual(result.files_processed, 1)
            self.assertEqual(result.entries_parsed, 1)
            self.assertEqual(result.patterns_identified, 0)
            self.assertEqual(result.unique_patterns, 0)
            self.assertEqual(result.issues_created, 0)
        finally:
            Path(file_path).unlink()

    def test_analyze_trace_files_full_success(self):
        """Should handle full successful analysis workflow."""
        # Mock components
        mock_entries = [
            ParsedEntry(
                timestamp="2024-01-01T12:00:00",
                entry_type="completion",
                data={"prompt": "test", "completion": "fix bug"},
            )
        ]
        mock_patterns = [
            ImprovementPattern(
                id="test_pattern_1",
                type="code_improvement",
                subtype="bug_fix",
                description="Fixed critical bug",
                confidence=0.9,
                evidence=["Code analysis"],
                suggested_action="Apply fix",
            )
        ]
        mock_dedup_result = Mock()
        mock_dedup_result.is_duplicate = False
        mock_issue_result = IssueCreationResult(
            success=True,
            issue_url="https://github.com/test/repo/issues/1",
            issue_number=1,
            title="Test Issue",
            metadata={"pattern_id": "test_pattern_1"},
        )

        self.analyzer.parser.parse_file.return_value = mock_entries  # type: ignore
        self.analyzer.pattern_extractor.extract_patterns.return_value = mock_patterns  # type: ignore  # type: ignore
        self.analyzer.deduplication_engine.is_duplicate.return_value = mock_dedup_result  # type: ignore
        self.analyzer.issue_generator.create_issue.return_value = mock_issue_result  # type: ignore
        self.analyzer.github_integration_enabled = True

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write('{"test": "data"}\n')
            file_path = f.name

        try:
            result = self.analyzer.analyze_trace_files([file_path])

            self.assertTrue(result.success)
            self.assertEqual(result.files_processed, 1)
            self.assertEqual(result.entries_parsed, 1)
            self.assertEqual(result.patterns_identified, 1)
            self.assertEqual(result.unique_patterns, 1)
            self.assertEqual(result.issues_created, 1)
            self.assertIsNotNone(result.detailed_results)
        finally:
            Path(file_path).unlink()

    def test_analyze_trace_files_with_exception(self):
        """Should handle exceptions gracefully."""
        self.analyzer.parser.parse_file.side_effect = Exception("Test error")  # type: ignore

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write('{"test": "data"}\n')
            file_path = f.name

        try:
            result = self.analyzer.analyze_trace_files([file_path])

            self.assertFalse(result.success)
            self.assertIsNotNone(result.error_message)
            error_msg = result.error_message
            assert error_msg is not None  # Type narrowing for pyright
            self.assertIn("Analysis failed", error_msg)
            self.assertIn("Test error", error_msg)
        finally:
            Path(file_path).unlink()

    def test_analyze_single_file(self):
        """Should analyze single file by delegating to analyze_trace_files."""
        with patch.object(self.analyzer, "analyze_trace_files") as mock_analyze:
            mock_result = AnalysisResult(success=True)
            mock_analyze.return_value = mock_result  # type: ignore

            result = self.analyzer.analyze_single_file("test_file.jsonl")

            mock_analyze.assert_called_once_with(["test_file.jsonl"], True)  # type: ignore
            self.assertEqual(result, mock_result)

    def test_get_analysis_summary_no_analysis(self):
        """Should return appropriate message when no analysis performed."""
        summary = self.analyzer.get_analysis_summary()

        self.assertEqual(summary["message"], "No analysis has been performed yet")

    def test_get_analysis_summary_with_analysis(self):
        """Should return comprehensive summary after analysis."""
        # Set up mock analysis result
        self.analyzer.last_analysis_result = AnalysisResult(
            success=True,
            files_processed=1,
            entries_parsed=5,
            patterns_identified=3,
            unique_patterns=2,
            issues_created=1,
        )

        # Mock component reports
        self.analyzer.deduplication_engine.get_deduplication_report.return_value = {  # type: ignore
            "duplicates_found": 1
        }
        self.analyzer.issue_generator.get_generation_statistics.return_value = {"issues_created": 1}  # type: ignore

        summary = self.analyzer.get_analysis_summary()

        self.assertIn("last_analysis", summary)
        self.assertIn("component_statistics", summary)
        self.assertIn("github_integration_enabled", summary)
        self.assertTrue(summary["last_analysis"]["success"])

    def test_reset_state(self):
        """Should reset internal state correctly."""
        # Set some state
        self.analyzer.last_analysis_result = AnalysisResult(success=True)

        self.analyzer.reset_state()

        self.assertIsNone(self.analyzer.last_analysis_result)
        self.analyzer.deduplication_engine.reset_cache.assert_called_once()  # type: ignore

    def test_parse_files_missing_file(self):
        """Should handle missing files gracefully."""
        with self.assertRaises(ValidationError) as context:
            self.analyzer._parse_files(["nonexistent_file.jsonl"])

        self.assertIn("Failed to parse any files", str(context.exception))

    def test_parse_files_with_validation_error(self):
        """Should handle validation errors during parsing."""
        self.analyzer.parser.parse_file.side_effect = ValidationError("Invalid JSON")  # type: ignore

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write("invalid json\n")
            file_path = f.name

        try:
            with self.assertRaises(ValidationError):
                self.analyzer._parse_files([file_path])
        finally:
            Path(file_path).unlink()

    def test_parse_files_partial_success(self):
        """Should continue with valid files when some fail."""
        mock_entries = [
            ParsedEntry(
                timestamp="2024-01-01T12:00:00", entry_type="completion", data={"prompt": "test"}
            )
        ]

        # First call fails, second succeeds
        self.analyzer.parser.parse_file.side_effect = [  # type: ignore
            ValidationError("Invalid JSON"),
            mock_entries,
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f1:
            f1.write("invalid json\n")
            file_path1 = f1.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f2:
            f2.write('{"test": "data"}\n')
            file_path2 = f2.name

        try:
            entries = self.analyzer._parse_files([file_path1, file_path2])

            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].data["prompt"], "test")
        finally:
            Path(file_path1).unlink()
            Path(file_path2).unlink()

    def test_extract_patterns(self):
        """Should delegate pattern extraction to pattern extractor."""
        mock_entries = cast(List[ParsedEntry], [Mock()])
        mock_patterns = [Mock()]
        self.analyzer.pattern_extractor.extract_patterns.return_value = mock_patterns  # type: ignore

        patterns = self.analyzer._extract_patterns(mock_entries)

        self.analyzer.pattern_extractor.extract_patterns.assert_called_once_with(mock_entries)  # type: ignore
        self.assertEqual(patterns, mock_patterns)

    def test_deduplicate_patterns(self):
        """Should deduplicate patterns using deduplication engine."""
        mock_pattern1 = Mock()
        mock_pattern2 = Mock()
        mock_result1 = Mock()
        mock_result1.is_duplicate = False
        mock_result2 = Mock()
        mock_result2.is_duplicate = True

        self.analyzer.deduplication_engine.is_duplicate.side_effect = [mock_result1, mock_result2]  # type: ignore

        unique_patterns = self.analyzer._deduplicate_patterns([mock_pattern1, mock_pattern2])

        self.assertEqual(len(unique_patterns), 1)
        self.assertEqual(unique_patterns[0], mock_pattern1)

    def test_create_issues_success(self):
        """Should create issues and return success counts."""
        mock_patterns = cast(List[ImprovementPattern], [Mock(), Mock()])
        mock_results = [
            IssueCreationResult(
                success=True,
                issue_url="url1",
                issue_number=1,
                title="Issue 1",
                metadata={"pattern_id": "1"},
            ),
            IssueCreationResult(
                success=False, error_message="Failed", title="Issue 2", metadata={"pattern_id": "2"}
            ),
        ]
        self.analyzer.issue_generator.create_issue.side_effect = mock_results  # type: ignore

        count, results = self.analyzer._create_issues(mock_patterns)

        self.assertEqual(count, 1)
        self.assertEqual(len(results), 2)
        self.assertTrue(results[0].success)
        self.assertFalse(results[1].success)

    def test_compile_detailed_results(self):
        """Should compile comprehensive detailed results."""
        mock_entries = cast(
            List[ParsedEntry], [Mock(entry_type="completion"), Mock(entry_type="error")]
        )
        mock_patterns = cast(
            List[ImprovementPattern],
            [Mock(type="code_improvement"), Mock(type="prompt_improvement")],
        )
        mock_unique_patterns = cast(List[ImprovementPattern], [Mock(type="code_improvement")])
        mock_issue_results = cast(
            List[IssueCreationResult], [Mock(success=True), Mock(success=False)]
        )

        # Mock component reports
        self.analyzer.deduplication_engine.get_deduplication_report.return_value = {"test": "data"}  # type: ignore
        self.analyzer.issue_generator.get_generation_statistics.return_value = {"test": "stats"}  # type: ignore

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write('{"test": "data"}\n')
            file_path = f.name

        try:
            result = self.analyzer._compile_detailed_results(
                [file_path], mock_entries, mock_patterns, mock_unique_patterns, mock_issue_results
            )

            self.assertIn("files", result)
            self.assertIn("entries", result)
            self.assertIn("patterns", result)
            self.assertIn("issues", result)
            self.assertIn("component_reports", result)

            # Check specific calculations
            self.assertEqual(result["files"]["total_count"], 1)
            self.assertEqual(result["entries"]["total_parsed"], 2)
            self.assertEqual(result["patterns"]["total_identified"], 2)
            self.assertEqual(result["patterns"]["unique_count"], 1)
            self.assertEqual(result["issues"]["creation_attempted"], 2)
            self.assertEqual(result["issues"]["successful"], 1)
            self.assertEqual(result["issues"]["failed"], 1)
        finally:
            Path(file_path).unlink()

    def test_count_by_type(self):
        """Should count items by specified type field."""
        mock_items = [
            Mock(entry_type="completion"),
            Mock(entry_type="completion"),
            Mock(entry_type="error"),
        ]

        counts = self.analyzer._count_by_type(mock_items, "entry_type")

        self.assertEqual(counts["completion"], 2)
        self.assertEqual(counts["error"], 1)

    def test_count_by_type_missing_field(self):
        """Should handle items missing the type field."""
        mock_items = [Mock(spec=[]), Mock(entry_type="completion")]

        counts = self.analyzer._count_by_type(mock_items, "entry_type")

        self.assertEqual(counts["unknown"], 1)
        self.assertEqual(counts["completion"], 1)


if __name__ == "__main__":
    unittest.main()
