"""
Integration tests for Claude-trace log analyzer system.

Testing pyramid: 30% integration tests focusing on component interactions.
Tests multiple components working together but with controlled environments.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from amplihack.analysis.claude_trace_analyzer import (
    AnalysisResult,
    ClaudeTraceLogAnalyzer,
    ClaudeTraceParser,
    GitHubIssueManager,
    ImprovementAnalyzer,
    ImprovementPattern,
)


class TestParserAnalyzerIntegration:
    """Test parser and analyzer working together."""

    def test_parse_and_analyze_real_trace_data(self):
        """Should parse real trace data and identify patterns."""
        # Create realistic claude-trace data
        trace_entries = [
            {
                "timestamp": "2025-01-27T12:00:00Z",
                "type": "tool_call",
                "tool": "Read",
                "parameters": {"file_path": "/src/utils.py"},
                "result": {
                    "success": True,
                    "content": "def bad_function():\n    for i in range(len(items)):\n        print(items[i])",
                },
            },
            {
                "timestamp": "2025-01-27T12:01:00Z",
                "type": "tool_call",
                "tool": "Edit",
                "parameters": {
                    "file_path": "/src/utils.py",
                    "old_string": "for i in range(len(items)):\n        print(items[i])",
                    "new_string": "for item in items:\n        print(item)",
                },
                "result": {"success": True},
            },
            {
                "timestamp": "2025-01-27T12:02:00Z",
                "type": "error",
                "error_type": "FileNotFoundError",
                "message": "No such file or directory: '/missing/file.py'",
                "context": {"tool": "Read", "file_path": "/missing/file.py"},
            },
            {
                "timestamp": "2025-01-27T12:03:00Z",
                "type": "tool_call",
                "tool": "Edit",
                "parameters": {
                    "file_path": "/src/main.py",
                    "old_string": "open('/missing/file.py')",
                    "new_string": "try:\n    open('/missing/file.py')\nexcept FileNotFoundError:\n    print('File not found')",
                },
                "result": {"success": True},
            },
        ]

        # Write trace data to temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            for entry in trace_entries:
                json.dump(entry, f)
                f.write("\n")
            trace_file = Path(f.name)

        # Parse and analyze
        parser = ClaudeTraceParser()
        analyzer = ImprovementAnalyzer()

        parsed_entries = parser.parse_file(trace_file)
        assert len(parsed_entries) == 4

        # Analyze for different pattern types
        code_patterns = analyzer.analyze_code_improvements(parsed_entries)
        error_patterns = analyzer.analyze_error_patterns(parsed_entries)

        # Should detect pythonic improvement
        assert len(code_patterns) >= 1
        pythonic_pattern = next((p for p in code_patterns if "range(len(" in str(p.evidence)), None)
        assert pythonic_pattern is not None
        assert (
            "enumerate" in pythonic_pattern.recommendation.lower()
            or "iteration" in pythonic_pattern.recommendation.lower()
        )

        # Should detect error handling improvement
        assert len(error_patterns) >= 1
        error_pattern = error_patterns[0]
        assert "FileNotFoundError" in error_pattern.evidence[0]
        assert (
            "try" in error_pattern.recommendation.lower()
            or "except" in error_pattern.recommendation.lower()
        )

    def test_analyzer_with_empty_parser_result(self):
        """Should handle empty parser results gracefully."""
        analyzer = ImprovementAnalyzer()

        patterns = analyzer.analyze_code_improvements([])
        assert patterns == []

        patterns = analyzer.analyze_error_patterns([])
        assert patterns == []

        patterns = analyzer.analyze_workflow_patterns([])
        assert patterns == []

    def test_parser_analyzer_with_corrupted_data(self):
        """Should handle partially corrupted trace data."""
        mixed_entries = [
            '{"timestamp": "2025-01-27T12:00:00Z", "type": "tool_call", "tool": "Read"}\n',
            "corrupted json line\n",
            '{"timestamp": "2025-01-27T12:01:00Z", "type": "error", "message": "Test error"}\n',
            "\n",  # empty line
            '{"incomplete": "entry"}\n',  # missing required fields
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.writelines(mixed_entries)
            trace_file = Path(f.name)

        parser = ClaudeTraceParser()
        analyzer = ImprovementAnalyzer()

        parsed_entries = parser.parse_file(trace_file)
        # Should parse valid entries and skip invalid ones
        assert len(parsed_entries) >= 2

        # Analyzer should handle mixed valid/invalid entries
        patterns = analyzer.analyze_error_patterns(parsed_entries)
        assert isinstance(patterns, list)


class TestAnalyzerGitHubIntegration:
    """Test analyzer and GitHub issue manager integration."""

    def test_create_issues_from_analysis_results(self):
        """Should create GitHub issues from analysis patterns."""
        patterns = [
            ImprovementPattern(
                category="code_quality",
                description="Replace range(len()) with enumerate",
                evidence=["for i in range(len(items)): items[i]"],
                recommendation="Use enumerate for better readability and performance",
                confidence=0.9,
                files_affected=["/src/utils.py"],
            ),
            ImprovementPattern(
                category="error_handling",
                description="Add exception handling for file operations",
                evidence=["open('/path/file.txt') without try-catch"],
                recommendation="Wrap file operations in try-except blocks",
                confidence=0.85,
                files_affected=["/src/main.py"],
            ),
        ]

        github_manager = GitHubIssueManager()

        with patch.object(github_manager, "is_duplicate_issue_by_pattern", return_value=False):
            with patch("amplihack.tools.github_issue.create_issue") as mock_create:
                mock_create.return_value = {
                    "success": True,
                    "issue_number": 130,
                    "issue_url": "https://github.com/test/repo/issues/130",
                }

                results = github_manager.create_issues_from_patterns(patterns)

                assert len(results) == 2
                assert all(r["success"] for r in results)
                assert mock_create.call_count == 2

                # Verify issue content formatting
                calls = mock_create.call_args_list
                first_call = calls[0].kwargs

                assert "Code Quality" in first_call["title"]
                assert "enumerate" in first_call["body"]
                assert "/src/utils.py" in first_call["body"]
                assert (
                    "confidence: 90%" in first_call["body"].lower() or "0.9" in first_call["body"]
                )

    def test_deduplication_prevents_duplicate_issues(self):
        """Should prevent creating duplicate issues."""
        patterns = [
            ImprovementPattern(
                category="code_quality",
                description="Use enumerate pattern",
                evidence=["range(len()) usage"],
                recommendation="Replace with enumerate",
                confidence=0.9,
                files_affected=["/test.py"],
            ),
            ImprovementPattern(
                category="code_quality",
                description="Use enumerate instead of range",  # Similar pattern
                evidence=["for i in range(len(items))"],
                recommendation="Use enumerate for iteration",
                confidence=0.8,
                files_affected=["/test2.py"],
            ),
        ]

        github_manager = GitHubIssueManager()

        # Mock deduplication - first is new, second is duplicate
        with patch.object(
            github_manager, "is_duplicate_issue_by_pattern", side_effect=[False, True]
        ):
            with patch("amplihack.tools.github_issue.create_issue") as mock_create:
                mock_create.return_value = {"success": True, "issue_number": 131}

                results = github_manager.create_issues_from_patterns(patterns)

                # Should only create one issue (second was duplicate)
                assert len(results) == 1
                assert mock_create.call_count == 1

    def test_github_api_error_handling(self):
        """Should handle GitHub API errors gracefully."""
        patterns = [
            ImprovementPattern(
                category="test",
                description="Test pattern",
                evidence=["test"],
                recommendation="test",
                confidence=0.8,
                files_affected=[],
            )
        ]

        github_manager = GitHubIssueManager()

        with patch.object(github_manager, "is_duplicate_issue_by_pattern", return_value=False):
            with patch("amplihack.tools.github_issue.create_issue") as mock_create:
                # Simulate API error
                mock_create.return_value = {
                    "success": False,
                    "error": "API rate limit exceeded. Try again later.",
                }

                results = github_manager.create_issues_from_patterns(patterns)

                assert len(results) == 1
                assert not results[0]["success"]
                assert "rate limit" in results[0]["error"].lower()


class TestFullSystemIntegration:
    """Test complete system with multiple directories and files."""

    def test_analyze_multiple_trace_directories(self):
        """Should analyze multiple .claude-trace directories."""
        # Create multiple trace directories with different data
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Directory 1: Code improvements
            dir1 = temp_path / "project1" / ".claude-trace"
            dir1.mkdir(parents=True)
            trace1 = dir1 / "session1.jsonl"

            entries1 = [
                {
                    "timestamp": "2025-01-27T10:00:00Z",
                    "type": "tool_call",
                    "tool": "Edit",
                    "parameters": {
                        "old_string": "if condition == True:",
                        "new_string": "if condition:",
                    },
                }
            ]

            with open(trace1, "w") as f:
                for entry in entries1:
                    json.dump(entry, f)
                    f.write("\n")

            # Directory 2: Error patterns
            dir2 = temp_path / "project2" / ".claude-trace"
            dir2.mkdir(parents=True)
            trace2 = dir2 / "session2.jsonl"

            entries2 = [
                {
                    "timestamp": "2025-01-27T11:00:00Z",
                    "type": "error",
                    "error_type": "AttributeError",
                    "message": "'NoneType' object has no attribute 'split'",
                },
                {
                    "timestamp": "2025-01-27T11:01:00Z",
                    "type": "tool_call",
                    "tool": "Edit",
                    "parameters": {
                        "old_string": "result.split()",
                        "new_string": "result.split() if result else []",
                    },
                },
            ]

            with open(trace2, "w") as f:
                for entry in entries2:
                    json.dump(entry, f)
                    f.write("\n")

            # Analyze all directories
            analyzer = ClaudeTraceLogAnalyzer()

            with patch.object(
                analyzer.github_manager, "create_issues_from_patterns"
            ) as mock_create:
                mock_create.return_value = [{"success": True, "issue_number": 140}]

                result = analyzer.analyze_directory_tree(temp_path)

                assert result.total_entries >= 3
                assert len(result.files_analyzed) == 2
                assert len(result.patterns) >= 1

                # Should have found patterns from both directories
                categories = {p.category for p in result.patterns}
                assert len(categories) >= 1

    def test_integration_with_existing_reflection_system(self):
        """Should integrate with existing reflection system metadata."""
        # Mock reflection system data
        reflection_data = {
            "session_id": "test_session_20250127_120000",
            "user_preferences": {"verbosity": "detailed", "focus": "code_quality"},
            "project_context": {"language": "python", "framework": "pytest"},
        }

        analyzer = ClaudeTraceLogAnalyzer(reflection_context=reflection_data)

        # Create trace data that should integrate with reflection context
        trace_entries = [
            {
                "timestamp": "2025-01-27T12:00:00Z",
                "type": "tool_call",
                "tool": "pytest",
                "parameters": {"args": ["-v", "tests/"]},
                "result": {"success": True, "tests_run": 45, "failures": 2},
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            for entry in trace_entries:
                json.dump(entry, f)
                f.write("\n")
            trace_file = Path(f.name)

        with patch.object(analyzer.github_manager, "create_issues_from_patterns") as mock_create:
            mock_create.return_value = []

            result = analyzer.analyze_files([trace_file])

            # Should include reflection context in analysis
            assert result.analysis_metadata["reflection_session"] == reflection_data["session_id"]
            assert (
                result.analysis_metadata["user_preferences"] == reflection_data["user_preferences"]
            )

    def test_concurrent_analysis_safety(self):
        """Should handle concurrent analysis requests safely."""
        import threading

        analyzer = ClaudeTraceLogAnalyzer()
        results = []

        def analyze_worker(worker_id):
            """Worker function for concurrent analysis."""
            # Create unique trace data for each worker
            trace_entries = [
                {
                    "timestamp": f"2025-01-27T12:0{worker_id}:00Z",
                    "type": "tool_call",
                    "tool": "Edit",
                    "parameters": {"file_path": f"/worker_{worker_id}.py"},
                }
            ]

            with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
                for entry in trace_entries:
                    json.dump(entry, f)
                    f.write("\n")
                trace_file = Path(f.name)

            with patch.object(
                analyzer.github_manager, "create_issues_from_patterns"
            ) as mock_create:
                mock_create.return_value = []
                result = analyzer.analyze_files([trace_file])
                results.append((worker_id, result))

        # Start multiple concurrent analysis threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=analyze_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=10)

        # All analyses should complete successfully
        assert len(results) == 3
        assert all(isinstance(result[1], AnalysisResult) for result in results)

    def test_performance_with_large_dataset(self):
        """Should handle large trace datasets efficiently."""
        # Create large trace file (1000 entries)
        large_entries = []
        for i in range(1000):
            entry = {
                "timestamp": f"2025-01-27T{i // 60:02d}:{i % 60:02d}:00Z",
                "type": "tool_call",
                "tool": "Read" if i % 2 == 0 else "Edit",
                "parameters": {"file_path": f"/file_{i % 10}.py"},
                "result": {"success": True},
            }
            large_entries.append(entry)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            for entry in large_entries:
                json.dump(entry, f)
                f.write("\n")
            large_trace_file = Path(f.name)

        analyzer = ClaudeTraceLogAnalyzer()

        start_time = datetime.now()

        with patch.object(analyzer.github_manager, "create_issues_from_patterns") as mock_create:
            mock_create.return_value = []
            result = analyzer.analyze_files([large_trace_file])

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        # Should process 1000 entries in reasonable time (< 10 seconds)
        assert processing_time < 10.0
        assert result.total_entries == 1000
        assert result.processing_time > 0
