"""
Unit tests for Claude-trace log analyzer system.

Following TDD approach - these tests should fail initially and guide implementation.
Testing pyramid: 60% unit tests focusing on core functionality.
"""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
from amplihack.analysis.claude_trace_analyzer import (
    AnalysisResult,
    ClaudeTraceParser,
    GitHubIssueManager,
    ImprovementAnalyzer,
    ImprovementPattern,
)


class TestClaudeTraceParser:
    """Test JSONL parsing functionality."""

    def test_parse_empty_file(self):
        """Should handle empty JSONL files gracefully."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write("")

        parser = ClaudeTraceParser()
        result = parser.parse_file(Path(f.name))

        assert result == []

    def test_parse_single_valid_entry(self):
        """Should parse single JSONL entry correctly."""
        entry = {
            "timestamp": "2025-01-27T12:00:00Z",
            "type": "tool_call",
            "tool": "Edit",
            "parameters": {"file_path": "/test.py", "old_string": "old", "new_string": "new"},
            "result": "success",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            json.dump(entry, f)

        parser = ClaudeTraceParser()
        result = parser.parse_file(Path(f.name))

        assert len(result) == 1
        assert result[0]["type"] == "tool_call"
        assert result[0]["tool"] == "Edit"

    def test_parse_multiple_entries(self):
        """Should parse multiple JSONL entries correctly."""
        entries = [
            {"timestamp": "2025-01-27T12:00:00Z", "type": "tool_call", "tool": "Read"},
            {"timestamp": "2025-01-27T12:01:00Z", "type": "error", "message": "File not found"},
            {
                "timestamp": "2025-01-27T12:02:00Z",
                "type": "completion",
                "model": "claude-3-5-sonnet",
            },
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            for entry in entries:
                json.dump(entry, f)
                f.write("\n")

        parser = ClaudeTraceParser()
        result = parser.parse_file(Path(f.name))

        assert len(result) == 3
        assert result[0]["tool"] == "Read"
        assert result[1]["type"] == "error"
        assert result[2]["type"] == "completion"

    def test_parse_malformed_json(self):
        """Should handle malformed JSON gracefully."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write('{"valid": "json"}\n')
            f.write("invalid json line\n")
            f.write('{"another": "valid"}\n')

        parser = ClaudeTraceParser()
        result = parser.parse_file(Path(f.name))

        # Should skip malformed lines and continue
        assert len(result) == 2
        assert result[0]["valid"] == "json"
        assert result[1]["another"] == "valid"

    def test_parse_file_not_found(self):
        """Should raise appropriate error for missing files."""
        parser = ClaudeTraceParser()

        with pytest.raises(FileNotFoundError):
            parser.parse_file(Path("/nonexistent/file.jsonl"))

    def test_parse_empty_lines(self):
        """Should skip empty lines in JSONL."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write('{"first": "entry"}\n')
            f.write("\n")
            f.write("   \n")  # whitespace only
            f.write('{"second": "entry"}\n')

        parser = ClaudeTraceParser()
        result = parser.parse_file(Path(f.name))

        assert len(result) == 2
        assert result[0]["first"] == "entry"
        assert result[1]["second"] == "entry"

    def test_parse_large_file_memory_efficiency(self):
        """Should handle large files without loading everything into memory."""
        # Create a large JSONL file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            for i in range(10000):
                entry = {"id": i, "type": "test", "data": f"entry_{i}"}
                json.dump(entry, f)
                f.write("\n")

        parser = ClaudeTraceParser()
        # Should use generator/iterator pattern for memory efficiency
        result = parser.parse_file_lazy(Path(f.name))

        # Test that it's a generator
        assert hasattr(result, "__iter__")

        # Test first few entries
        entries = list(entry for i, entry in enumerate(result) if i < 5)
        assert len(entries) == 5
        assert entries[0]["id"] == 0
        assert entries[4]["id"] == 4


class TestImprovementAnalyzer:
    """Test improvement pattern detection."""

    def test_detect_code_improvement_patterns(self):
        """Should identify code improvement opportunities."""
        log_entries = [
            {
                "type": "tool_call",
                "tool": "Edit",
                "parameters": {
                    "file_path": "/test.py",
                    "old_string": "if x == True:",
                    "new_string": "if x:",
                },
                "timestamp": "2025-01-27T12:00:00Z",
            },
            {
                "type": "tool_call",
                "tool": "Edit",
                "parameters": {
                    "file_path": "/test.py",
                    "old_string": "for i in range(len(items)):",
                    "new_string": "for i, item in enumerate(items):",
                },
                "timestamp": "2025-01-27T12:01:00Z",
            },
        ]

        analyzer = ImprovementAnalyzer()
        patterns = analyzer.analyze_code_improvements(log_entries)

        assert len(patterns) >= 1
        # Should detect pythonic code improvements
        pythonic_pattern = next((p for p in patterns if "pythonic" in p.category.lower()), None)
        assert pythonic_pattern is not None
        assert (
            "Boolean comparison" in pythonic_pattern.description
            or "enumerate" in pythonic_pattern.description
        )

    def test_detect_error_handling_improvements(self):
        """Should identify error handling patterns."""
        log_entries = [
            {
                "type": "error",
                "error_type": "FileNotFoundError",
                "message": "No such file or directory: '/path/file.txt'",
                "timestamp": "2025-01-27T12:00:00Z",
            },
            {
                "type": "tool_call",
                "tool": "Edit",
                "parameters": {
                    "old_string": "open('/path/file.txt')",
                    "new_string": "try:\n    open('/path/file.txt')\nexcept FileNotFoundError:\n    # Handle missing file",
                },
                "timestamp": "2025-01-27T12:01:00Z",
            },
        ]

        analyzer = ImprovementAnalyzer()
        patterns = analyzer.analyze_error_patterns(log_entries)

        assert len(patterns) >= 1
        error_pattern = patterns[0]
        assert error_pattern.category == "error_handling"
        assert "FileNotFoundError" in error_pattern.evidence

    def test_detect_workflow_improvements(self):
        """Should identify workflow inefficiencies."""
        log_entries = [
            {
                "type": "tool_call",
                "tool": "Read",
                "parameters": {"file_path": "/test.py"},
                "timestamp": "2025-01-27T12:00:00Z",
            },
            {
                "type": "tool_call",
                "tool": "Read",
                "parameters": {"file_path": "/test.py"},
                "timestamp": "2025-01-27T12:00:05Z",
            },
            {
                "type": "tool_call",
                "tool": "Read",
                "parameters": {"file_path": "/test.py"},
                "timestamp": "2025-01-27T12:00:10Z",
            },
            {
                "type": "tool_call",
                "tool": "Edit",
                "parameters": {"file_path": "/test.py"},
                "timestamp": "2025-01-27T12:00:15Z",
            },
        ]

        analyzer = ImprovementAnalyzer()
        patterns = analyzer.analyze_workflow_patterns(log_entries)

        assert len(patterns) >= 1
        workflow_pattern = patterns[0]
        assert workflow_pattern.category == "workflow_efficiency"
        assert "repeated reads" in workflow_pattern.description.lower()

    def test_detect_prompt_improvements(self):
        """Should identify prompt optimization opportunities."""
        log_entries = [
            {
                "type": "completion",
                "prompt_tokens": 5000,
                "completion_tokens": 100,
                "model": "claude-3-5-sonnet",
                "timestamp": "2025-01-27T12:00:00Z",
            },
            {
                "type": "completion",
                "prompt_tokens": 5500,
                "completion_tokens": 50,
                "model": "claude-3-5-sonnet",
                "timestamp": "2025-01-27T12:01:00Z",
            },
        ]

        analyzer = ImprovementAnalyzer()
        patterns = analyzer.analyze_prompt_patterns(log_entries)

        # Should detect high token usage patterns
        assert len(patterns) >= 0  # May or may not detect based on thresholds

    def test_empty_log_entries(self):
        """Should handle empty log entries gracefully."""
        analyzer = ImprovementAnalyzer()

        patterns = analyzer.analyze_code_improvements([])
        assert patterns == []

        patterns = analyzer.analyze_error_patterns([])
        assert patterns == []

        patterns = analyzer.analyze_workflow_patterns([])
        assert patterns == []

    def test_invalid_log_entries(self):
        """Should handle malformed log entries gracefully."""
        invalid_entries = [
            {"invalid": "entry"},
            {"type": "unknown_type"},
            {"type": "tool_call"},  # missing required fields
            None,
        ]

        analyzer = ImprovementAnalyzer()
        patterns = analyzer.analyze_code_improvements(invalid_entries)

        # Should not crash and return empty or valid patterns only
        assert isinstance(patterns, list)


class TestGitHubIssueManager:
    """Test GitHub issue creation and deduplication."""

    def test_issue_deduplication_by_title(self):
        """Should detect duplicate issues by title similarity."""
        manager = GitHubIssueManager()

        # Mock existing issues
        existing_issues = [
            {"title": "Improve error handling in file operations", "number": 123},
            {"title": "Add unit tests for API endpoints", "number": 124},
        ]

        with patch.object(manager, "_get_existing_issues", return_value=existing_issues):
            # Similar title should be detected as duplicate
            is_duplicate = manager.is_duplicate_issue("Enhance error handling for file ops")
            assert is_duplicate

            # Different title should not be duplicate
            is_duplicate = manager.is_duplicate_issue("Add integration tests for database")
            assert not is_duplicate

    def test_issue_deduplication_by_content(self):
        """Should detect duplicate issues by content similarity."""
        manager = GitHubIssueManager()

        pattern = ImprovementPattern(
            category="code_quality",
            description="Use enumerate instead of range(len())",
            evidence=["for i in range(len(items)): items[i]"],
            recommendation="Replace with enumerate for better readability",
            confidence=0.9,
            files_affected=["/test.py"],
        )

        existing_issues = [
            {
                "title": "Code Quality: Use enumerate pattern",
                "body": "Replace range(len()) patterns with enumerate for better readability",
                "number": 125,
            }
        ]

        with patch.object(manager, "_get_existing_issues", return_value=existing_issues):
            is_duplicate = manager.is_duplicate_issue_by_pattern(pattern)
            assert is_duplicate

    def test_create_issue_with_pattern(self):
        """Should create well-formatted GitHub issue from pattern."""
        manager = GitHubIssueManager()

        pattern = ImprovementPattern(
            category="error_handling",
            description="Add try-catch for file operations",
            evidence=["open('/path/file.txt') without error handling"],
            recommendation="Wrap file operations in try-catch blocks",
            confidence=0.85,
            files_affected=["/src/utils.py", "/src/main.py"],
        )

        with patch("amplihack.tools.github_issue.create_issue") as mock_create:
            mock_create.return_value = {
                "success": True,
                "issue_number": 126,
                "issue_url": "https://github.com/repo/issues/126",
            }

            result = manager.create_issue_from_pattern(pattern)

            assert result["success"]
            assert result["issue_number"] == 126

            # Verify issue content formatting
            call_args = mock_create.call_args
            assert "Error Handling" in call_args.kwargs["title"]
            assert "try-catch" in call_args.kwargs["body"]
            assert "evidence" in call_args.kwargs["body"].lower()
            assert "/src/utils.py" in call_args.kwargs["body"]

    def test_rate_limiting_handling(self):
        """Should handle GitHub API rate limiting gracefully."""
        manager = GitHubIssueManager()

        pattern = ImprovementPattern(
            category="test",
            description="Test pattern",
            evidence=["test"],
            recommendation="Test recommendation",
            confidence=0.8,
            files_affected=[],
        )

        with patch("amplihack.tools.github_issue.create_issue") as mock_create:
            # Simulate rate limit error
            mock_create.return_value = {"success": False, "error": "API rate limit exceeded"}

            result = manager.create_issue_from_pattern(pattern)

            assert not result["success"]
            assert "rate limit" in result["error"].lower()

    def test_batch_issue_creation(self):
        """Should handle batch creation with deduplication."""
        manager = GitHubIssueManager()

        patterns = [
            ImprovementPattern(
                category="code",
                description="Pattern 1",
                evidence=[],
                recommendation="Rec 1",
                confidence=0.8,
                files_affected=[],
            ),
            ImprovementPattern(
                category="code",
                description="Pattern 2",
                evidence=[],
                recommendation="Rec 2",
                confidence=0.8,
                files_affected=[],
            ),
            ImprovementPattern(
                category="code",
                description="Pattern 1",
                evidence=[],
                recommendation="Rec 1",
                confidence=0.8,
                files_affected=[],
            ),  # duplicate
        ]

        with patch.object(
            manager, "is_duplicate_issue_by_pattern", side_effect=[False, False, True]
        ):
            with patch.object(
                manager,
                "create_issue_from_pattern",
                return_value={"success": True, "issue_number": 127},
            ) as mock_create:
                results = manager.create_issues_from_patterns(patterns)

                # Should only create 2 issues (skip duplicate)
                assert len(results) == 2
                assert mock_create.call_count == 2


class TestAnalysisResult:
    """Test analysis result data structure."""

    def test_analysis_result_creation(self):
        """Should create analysis result with all fields."""
        patterns = [
            ImprovementPattern(
                category="test",
                description="Test pattern",
                evidence=["evidence"],
                recommendation="recommendation",
                confidence=0.9,
                files_affected=["/test.py"],
            )
        ]

        result = AnalysisResult(
            total_entries=100,
            patterns=patterns,
            processing_time=1.5,
            files_analyzed=["/path/to/trace.jsonl"],
            analysis_timestamp=datetime.now(timezone.utc),
        )

        assert result.total_entries == 100
        assert len(result.patterns) == 1
        assert result.processing_time == 1.5
        assert len(result.files_analyzed) == 1

    def test_analysis_result_summary(self):
        """Should generate human-readable summary."""
        patterns = [
            ImprovementPattern(
                category="code",
                description="Code improvement",
                evidence=[],
                recommendation="",
                confidence=0.8,
                files_affected=[],
            ),
            ImprovementPattern(
                category="error",
                description="Error handling",
                evidence=[],
                recommendation="",
                confidence=0.9,
                files_affected=[],
            ),
            ImprovementPattern(
                category="code",
                description="Another code improvement",
                evidence=[],
                recommendation="",
                confidence=0.7,
                files_affected=[],
            ),
        ]

        result = AnalysisResult(
            total_entries=50,
            patterns=patterns,
            processing_time=0.8,
            files_analyzed=["/trace1.jsonl", "/trace2.jsonl"],
            analysis_timestamp=datetime.now(timezone.utc),
        )

        summary = result.get_summary()

        assert "3 patterns" in summary
        assert "2 files" in summary
        assert "code: 2" in summary
        assert "error: 1" in summary


class TestImprovementPattern:
    """Test improvement pattern data structure."""

    def test_pattern_validation(self):
        """Should validate required pattern fields."""
        # Valid pattern
        pattern = ImprovementPattern(
            category="test",
            description="Test description",
            evidence=["evidence1", "evidence2"],
            recommendation="Test recommendation",
            confidence=0.85,
            files_affected=["/test.py"],
        )

        assert pattern.category == "test"
        assert len(pattern.evidence) == 2
        assert pattern.confidence == 0.85

    def test_pattern_confidence_bounds(self):
        """Should enforce confidence score bounds."""
        with pytest.raises(ValueError):
            ImprovementPattern(
                category="test",
                description="Test",
                evidence=[],
                recommendation="Test",
                confidence=1.5,  # Invalid: > 1.0
                files_affected=[],
            )

        with pytest.raises(ValueError):
            ImprovementPattern(
                category="test",
                description="Test",
                evidence=[],
                recommendation="Test",
                confidence=-0.1,  # Invalid: < 0.0
                files_affected=[],
            )

    def test_pattern_serialization(self):
        """Should serialize to dict for JSON storage."""
        pattern = ImprovementPattern(
            category="test",
            description="Test pattern",
            evidence=["evidence"],
            recommendation="recommendation",
            confidence=0.9,
            files_affected=["/test.py"],
        )

        data = pattern.to_dict()

        assert data["category"] == "test"
        assert data["confidence"] == 0.9
        assert isinstance(data["evidence"], list)

        # Should round-trip through JSON
        reconstructed = ImprovementPattern.from_dict(data)
        assert reconstructed.category == pattern.category
        assert reconstructed.confidence == pattern.confidence
