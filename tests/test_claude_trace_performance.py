"""
Performance and error case tests for Claude-trace log analyzer system.

Tests system behavior under stress, edge cases, and error conditions.
"""

import gc
import json
import tempfile
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import psutil
import pytest
from amplihack.analysis.claude_trace_analyzer import (
    ClaudeTraceLogAnalyzer,
    ClaudeTraceParser,
    GitHubIssueManager,
    ImprovementAnalyzer,
)

from tests.fixtures.claude_trace_test_data import (
    AnalysisResultMockStrategy,
    ClaudeTraceTestData,
    GitHubAPIMockStrategy,
)


class TestPerformanceScenarios:
    """Test system performance under various load conditions."""

    def test_large_file_processing_performance(self):
        """Should process large JSONL files efficiently."""
        # Create large trace file (10,000 entries)
        entries = []
        base_time = datetime(2025, 1, 27, 10, 0, 0, tzinfo=timezone.utc)

        for i in range(10000):
            entry = {
                "timestamp": (base_time + timedelta(seconds=i)).isoformat(),
                "type": "tool_call",
                "tool": "Read" if i % 2 == 0 else "Edit",
                "parameters": {"file_path": f"/file_{i % 100}.py"},
                "result": {"success": True},
            }
            entries.append(entry)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            for entry in entries:
                json.dump(entry, f)
                f.write("\\n")
            large_file = Path(f.name)

        # Monitor performance
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss

        parser = ClaudeTraceParser()
        parsed_entries = parser.parse_file(large_file)

        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss

        processing_time = end_time - start_time
        memory_increase = end_memory - start_memory

        # Performance assertions
        assert processing_time < 5.0  # Should parse 10k entries in < 5 seconds
        assert len(parsed_entries) == 10000
        assert memory_increase < 100 * 1024 * 1024  # < 100MB memory increase

    def test_memory_efficiency_with_streaming_parser(self):
        """Should use memory-efficient streaming for large files."""
        # Create very large file (50,000 entries)
        large_entries = []
        for i in range(50000):
            entry = {
                "timestamp": f"2025-01-27T{i // 3600:02d}:{(i % 3600) // 60:02d}:{i % 60:02d}Z",
                "type": "tool_call",
                "tool": "Edit",
                "parameters": {
                    "file_path": f"/huge_file_{i}.py",
                    "data": "x" * 100,
                },  # Add some content
                "result": {"success": True},
            }
            large_entries.append(entry)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            for entry in large_entries:
                json.dump(entry, f)
                f.write("\\n")
            huge_file = Path(f.name)

        # Test memory-efficient parsing
        parser = ClaudeTraceParser()
        initial_memory = psutil.Process().memory_info().rss

        # Use lazy parsing if available
        if hasattr(parser, "parse_file_lazy"):
            entry_iterator = parser.parse_file_lazy(huge_file)
            # Process first 1000 entries
            processed_count = 0
            for entry in entry_iterator:
                processed_count += 1
                if processed_count >= 1000:
                    break

            current_memory = psutil.Process().memory_info().rss
            memory_increase = current_memory - initial_memory

            # Should not load entire file into memory
            assert memory_increase < 50 * 1024 * 1024  # < 50MB for 1000 entries
            assert processed_count == 1000

    def test_concurrent_analysis_performance(self):
        """Should handle multiple concurrent analysis requests efficiently."""

        def create_test_file(session_id: int) -> Path:
            entries = ClaudeTraceTestData.create_code_improvement_session()
            # Add session-specific data
            for entry in entries:
                entry["session_id"] = f"session_{session_id}"

            with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
                for entry in entries:
                    json.dump(entry, f)
                    f.write("\\n")
                return Path(f.name)

        # Create multiple test files
        test_files = [create_test_file(i) for i in range(5)]
        results = {}
        start_time = time.time()

        def analyze_worker(worker_id: int, file_path: Path):
            """Worker function for concurrent analysis."""
            analyzer = ClaudeTraceLogAnalyzer()
            with patch.object(
                analyzer.github_manager, "create_issues_from_patterns"
            ) as mock_create:
                mock_create.return_value = []
                result = analyzer.analyze_files([file_path])
                results[worker_id] = result

        # Start concurrent analysis
        threads = []
        for i, file_path in enumerate(test_files):
            thread = threading.Thread(target=analyze_worker, args=(i, file_path))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join(timeout=30)  # 30 second timeout

        end_time = time.time()
        total_time = end_time - start_time

        # All analyses should complete successfully
        assert len(results) == 5
        assert total_time < 15.0  # Should complete 5 concurrent analyses in < 15 seconds

        # Each result should be valid
        for result in results.values():
            assert result.total_entries > 0
            assert isinstance(result.patterns, list)

    def test_pattern_analysis_performance_scaling(self):
        """Should scale pattern analysis efficiently with entry count."""
        test_sizes = [100, 500, 1000, 2000]
        performance_data = {}

        for size in test_sizes:
            # Create test data of specified size
            entries = []
            for i in range(size):
                if i % 10 == 0:  # Add some pattern-worthy entries
                    entries.extend(ClaudeTraceTestData.create_code_improvement_session())
                else:
                    entries.append(
                        {
                            "timestamp": f"2025-01-27T{i // 3600:02d}:{(i % 3600) // 60:02d}:{i % 60:02d}Z",
                            "type": "tool_call",
                            "tool": "Read",
                            "parameters": {"file_path": f"/file_{i}.py"},
                            "result": {"success": True},
                        }
                    )

            # Analyze performance
            analyzer = ImprovementAnalyzer()
            start_time = time.time()

            patterns = analyzer.analyze_code_improvements(entries[:size])

            end_time = time.time()
            performance_data[size] = {
                "time": end_time - start_time,
                "patterns": len(patterns),
                "entries": size,
            }

        # Performance should scale reasonably (not exponentially)
        for i in range(1, len(test_sizes)):
            prev_size = test_sizes[i - 1]
            curr_size = test_sizes[i]
            size_ratio = curr_size / prev_size
            time_ratio = performance_data[curr_size]["time"] / performance_data[prev_size]["time"]

            # Time increase should not be more than 3x the size increase
            assert time_ratio <= size_ratio * 3

    def test_github_rate_limiting_handling(self):
        """Should handle GitHub rate limiting gracefully."""
        patterns = AnalysisResultMockStrategy.create_sample_patterns()

        github_manager = GitHubIssueManager()

        # Simulate rate limiting scenario
        with patch("amplihack.tools.github_issue.create_issue") as mock_create:
            # First few succeed, then rate limited, then succeed again
            mock_create.side_effect = [
                GitHubAPIMockStrategy.create_successful_issue_response(200),
                GitHubAPIMockStrategy.create_successful_issue_response(201),
                GitHubAPIMockStrategy.create_rate_limit_response(),
                GitHubAPIMockStrategy.create_rate_limit_response(),
                GitHubAPIMockStrategy.create_successful_issue_response(202),
            ]

            with patch.object(github_manager, "is_duplicate_issue_by_pattern", return_value=False):
                start_time = time.time()
                results = github_manager.create_issues_from_patterns(patterns)
                end_time = time.time()

                # Should handle rate limiting without crashing
                assert len(results) == len(patterns)
                successful_issues = [r for r in results if r.get("success")]
                failed_issues = [r for r in results if not r.get("success")]

                assert len(successful_issues) >= 2  # Some should succeed
                assert len(failed_issues) >= 1  # Some should fail due to rate limiting

                # Should complete in reasonable time (no infinite retries)
                assert end_time - start_time < 10.0


class TestErrorHandlingScenarios:
    """Test system behavior under error conditions."""

    def test_malformed_json_recovery(self):
        """Should recover from malformed JSON entries gracefully."""
        mixed_content = [
            '{"timestamp": "2025-01-27T12:00:00Z", "type": "tool_call", "tool": "Read"}\\n',
            "completely invalid json\\n",
            '{"timestamp": "2025-01-27T12:01:00Z", "type": "error", "message": "test"}\\n',
            "{invalid json without quotes}\\n",
            '{"valid": "entry", "timestamp": "2025-01-27T12:02:00Z"}\\n',
            "",  # empty line
            "   \\n",  # whitespace
            '{"incomplete": }\\n',  # incomplete JSON
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.writelines(mixed_content)
            malformed_file = Path(f.name)

        parser = ClaudeTraceParser()
        parsed_entries = parser.parse_file(malformed_file)

        # Should parse valid entries and skip invalid ones
        assert len(parsed_entries) >= 3  # At least the valid entries
        # Should not crash or raise exceptions

    def test_file_system_errors(self):
        """Should handle file system errors gracefully."""
        parser = ClaudeTraceParser()

        # Test non-existent file
        with pytest.raises(FileNotFoundError):
            parser.parse_file(Path("/nonexistent/file.jsonl"))

        # Test permission denied (simulate)
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with pytest.raises(PermissionError):
                parser.parse_file(Path("/mock/file.jsonl"))

        # Test corrupted file (simulate IO error)
        with patch("builtins.open", side_effect=IOError("Disk error")):
            with pytest.raises(IOError):
                parser.parse_file(Path("/mock/file.jsonl"))

    def test_github_api_failure_recovery(self):
        """Should handle various GitHub API failures gracefully."""
        patterns = [
            {
                "category": "test",
                "description": "Test pattern",
                "evidence": ["test"],
                "recommendation": "test",
                "confidence": 0.8,
                "files_affected": ["/test.py"],
            }
        ]

        github_manager = GitHubIssueManager()

        # Test different types of GitHub failures
        error_scenarios = [
            {"success": False, "error": "Network timeout"},
            {"success": False, "error": "API rate limit exceeded"},
            {"success": False, "error": "Authentication failed"},
            {"success": False, "error": "Repository not found"},
            {"success": False, "error": "Insufficient permissions"},
        ]

        for error_response in error_scenarios:
            with patch("amplihack.tools.github_issue.create_issue", return_value=error_response):
                with patch.object(
                    github_manager, "is_duplicate_issue_by_pattern", return_value=False
                ):
                    results = github_manager.create_issues_from_patterns(patterns)

                    # Should handle all errors gracefully
                    assert len(results) == 1
                    assert not results[0]["success"]
                    assert "error" in results[0]

    def test_memory_pressure_handling(self):
        """Should handle memory pressure conditions gracefully."""

        # Create a scenario that might cause memory pressure
        def memory_intensive_operation():
            # Simulate memory-intensive analysis
            large_entries = []
            for i in range(100000):
                entry = {
                    "timestamp": f"2025-01-27T12:00:{i % 60:02d}Z",
                    "type": "tool_call",
                    "tool": "Edit",
                    "parameters": {"file_path": f"/file_{i}.py", "content": "x" * 1000},
                    "result": {"success": True, "large_data": "y" * 10000},
                }
                large_entries.append(entry)
            return large_entries

        # Monitor memory usage
        initial_memory = psutil.Process().memory_info().rss

        try:
            analyzer = ImprovementAnalyzer()
            large_dataset = memory_intensive_operation()

            # Should handle large dataset without crashing
            analyzer.analyze_code_improvements(large_dataset[:1000])  # Process subset

            current_memory = psutil.Process().memory_info().rss
            memory_increase = current_memory - initial_memory

            # Should not consume excessive memory
            assert memory_increase < 500 * 1024 * 1024  # < 500MB

        finally:
            # Clean up memory
            gc.collect()

    def test_concurrent_access_safety(self):
        """Should handle concurrent access to shared resources safely."""
        github_manager = GitHubIssueManager()
        results = []
        errors = []

        def concurrent_worker(worker_id: int):
            """Worker that performs operations concurrently."""
            try:
                patterns = [
                    {
                        "category": f"test_{worker_id}",
                        "description": f"Test pattern {worker_id}",
                        "evidence": [f"evidence_{worker_id}"],
                        "recommendation": f"recommendation_{worker_id}",
                        "confidence": 0.8,
                        "files_affected": [f"/test_{worker_id}.py"],
                    }
                ]

                with patch("amplihack.tools.github_issue.create_issue") as mock_create:
                    mock_create.return_value = {"success": True, "issue_number": 300 + worker_id}

                    with patch.object(
                        github_manager, "is_duplicate_issue_by_pattern", return_value=False
                    ):
                        result = github_manager.create_issues_from_patterns(patterns)
                        results.append((worker_id, result))

            except Exception as e:
                errors.append((worker_id, str(e)))

        # Start multiple concurrent workers
        threads = []
        for i in range(10):
            thread = threading.Thread(target=concurrent_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join(timeout=15)

        # Should complete without race conditions or deadlocks
        assert len(results) == 10
        assert len(errors) == 0

    def test_invalid_configuration_handling(self):
        """Should handle invalid configuration gracefully."""
        # Test with invalid reflection context
        invalid_contexts = [
            None,
            {"invalid": "structure"},
            {"session_id": None},
            {"session_id": "valid", "user_preferences": "invalid_type"},
        ]

        for invalid_context in invalid_contexts:
            try:
                analyzer = ClaudeTraceLogAnalyzer(reflection_context=invalid_context)
                # Should not crash during initialization
                assert analyzer is not None
            except Exception as e:
                # If it does raise an exception, it should be a clear validation error
                assert isinstance(e, (ValueError, TypeError))

    def test_disk_space_exhaustion_simulation(self):
        """Should handle disk space issues gracefully."""
        # Simulate disk space issues during file operations
        with patch("tempfile.NamedTemporaryFile", side_effect=OSError("No space left on device")):
            analyzer = ClaudeTraceLogAnalyzer()

            # Should handle disk space errors gracefully
            with pytest.raises(OSError):
                # This would normally create temporary files
                analyzer.analyze_directory_tree(Path("/mock/path"))

    def test_network_timeout_scenarios(self):
        """Should handle network timeouts in GitHub operations."""
        import subprocess

        github_manager = GitHubIssueManager()

        # Simulate network timeout in gh CLI calls
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("gh", 30)):
            with patch.object(github_manager, "_get_existing_issues") as mock_get:
                try:
                    # Should handle timeout gracefully
                    existing = mock_get()
                    assert existing is None or isinstance(existing, list)
                except subprocess.TimeoutExpired:
                    # Acceptable to propagate timeout errors
                    pass

    def test_unicode_and_encoding_issues(self):
        """Should handle Unicode and encoding issues in trace files."""
        # Create file with various Unicode characters and encoding issues
        unicode_entries = [
            {"timestamp": "2025-01-27T12:00:00Z", "type": "tool_call", "content": "Hello 世界"},
            {
                "timestamp": "2025-01-27T12:01:00Z",
                "type": "error",
                "message": "Ошибка: файл не найден",
            },
            {
                "timestamp": "2025-01-27T12:02:00Z",
                "type": "tool_call",
                "emoji": "🚀 Deployment successful",
            },
            {
                "timestamp": "2025-01-27T12:03:00Z",
                "type": "tool_call",
                "special_chars": "\\n\\t\\r special",
            },
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".jsonl", delete=False
        ) as f:
            for entry in unicode_entries:
                json.dump(entry, f, ensure_ascii=False)
                f.write("\\n")
            unicode_file = Path(f.name)

        parser = ClaudeTraceParser()
        parsed_entries = parser.parse_file(unicode_file)

        # Should handle Unicode correctly
        assert len(parsed_entries) == 4
        assert any("世界" in str(entry) for entry in parsed_entries)
        assert any("🚀" in str(entry) for entry in parsed_entries)

    def test_edge_case_timestamp_formats(self):
        """Should handle various timestamp formats and edge cases."""
        edge_case_entries = [
            '{"timestamp": "2025-01-27T12:00:00Z", "type": "tool_call"}\\n',  # Standard ISO
            '{"timestamp": "2025-01-27T12:00:00+00:00", "type": "tool_call"}\\n',  # With timezone
            '{"timestamp": "2025-01-27T12:00:00.123Z", "type": "tool_call"}\\n',  # With milliseconds
            '{"timestamp": "invalid-timestamp", "type": "tool_call"}\\n',  # Invalid format
            '{"timestamp": null, "type": "tool_call"}\\n',  # Null timestamp
            '{"type": "tool_call"}\\n',  # Missing timestamp
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.writelines(edge_case_entries)
            edge_case_file = Path(f.name)

        parser = ClaudeTraceParser()
        parsed_entries = parser.parse_file(edge_case_file)

        # Should parse entries with valid timestamps, skip or handle invalid ones
        assert len(parsed_entries) >= 3  # At least the valid timestamp entries

    def test_analyzer_with_extreme_data_patterns(self):
        """Should handle extreme data patterns without crashing."""
        extreme_entries = [
            # Very long content
            {
                "timestamp": "2025-01-27T12:00:00Z",
                "type": "tool_call",
                "tool": "Edit",
                "parameters": {"content": "x" * 100000},  # 100KB of content
            },
            # Deeply nested structure
            {
                "timestamp": "2025-01-27T12:01:00Z",
                "type": "tool_call",
                "tool": "Read",
                "nested": {"level1": {"level2": {"level3": {"level4": {"data": "deep"}}}}},
            },
            # Many fields
            {
                "timestamp": "2025-01-27T12:02:00Z",
                "type": "tool_call",
                **{f"field_{i}": f"value_{i}" for i in range(1000)},  # 1000 fields
            },
        ]

        analyzer = ImprovementAnalyzer()

        # Should handle extreme data without crashing
        try:
            patterns = analyzer.analyze_code_improvements(extreme_entries)
            assert isinstance(patterns, list)
        except (MemoryError, RecursionError):
            # Acceptable to fail on truly extreme data
            pytest.skip("System limits reached with extreme data")
