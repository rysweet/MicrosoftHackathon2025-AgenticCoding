"""
End-to-end tests for Claude-trace log analyzer system.

Testing pyramid: 10% E2E tests focusing on complete workflow validation.
Tests the entire system from trace files to GitHub issues in real-world scenarios.
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from amplihack.analysis.claude_trace_analyzer import ClaudeTraceLogAnalyzer


class TestCompleteWorkflow:
    """Test complete workflow from trace discovery to issue creation."""

    @pytest.fixture
    def mock_github_environment(self):
        """Setup mock GitHub environment."""
        with patch("subprocess.run") as mock_run:
            # Mock successful gh auth check
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
            yield mock_run

    @pytest.fixture
    def sample_project_structure(self):
        """Create sample project with multiple claude-trace directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create realistic project structure
            (project_root / "src").mkdir()
            (project_root / "tests").mkdir()
            (project_root / "docs").mkdir()

            # Session 1: Initial development with code quality issues
            session1_dir = project_root / ".claude-trace"
            session1_dir.mkdir()
            session1_file = session1_dir / "session_20250127_100000.jsonl"

            session1_entries = [
                {
                    "timestamp": "2025-01-27T10:00:00Z",
                    "type": "tool_call",
                    "tool": "Read",
                    "parameters": {"file_path": str(project_root / "src" / "main.py")},
                    "result": {
                        "success": True,
                        "content": "def process_items(items):\\n    for i in range(len(items)):\\n        if items[i] == True:\\n            print(items[i])",
                    },
                },
                {
                    "timestamp": "2025-01-27T10:01:00Z",
                    "type": "tool_call",
                    "tool": "Edit",
                    "parameters": {
                        "file_path": str(project_root / "src" / "main.py"),
                        "old_string": "for i in range(len(items)):",
                        "new_string": "for item in items:",
                    },
                    "result": {"success": True},
                },
                {
                    "timestamp": "2025-01-27T10:02:00Z",
                    "type": "tool_call",
                    "tool": "Edit",
                    "parameters": {
                        "file_path": str(project_root / "src" / "main.py"),
                        "old_string": "if items[i] == True:",
                        "new_string": "if item:",
                    },
                    "result": {"success": True},
                },
            ]

            with open(session1_file, "w") as f:
                for entry in session1_entries:
                    json.dump(entry, f)
                    f.write("\\n")

            # Session 2: Bug fixing with error handling improvements
            session2_dir = project_root / "debug_session" / ".claude-trace"
            session2_dir.mkdir(parents=True)
            session2_file = session2_dir / "session_20250127_140000.jsonl"

            session2_entries = [
                {
                    "timestamp": "2025-01-27T14:00:00Z",
                    "type": "error",
                    "error_type": "FileNotFoundError",
                    "message": "No such file or directory: '/config/settings.json'",
                    "context": {
                        "tool": "Read",
                        "file_path": "/config/settings.json",
                        "line_number": 45,
                    },
                },
                {
                    "timestamp": "2025-01-27T14:01:00Z",
                    "type": "tool_call",
                    "tool": "Edit",
                    "parameters": {
                        "file_path": str(project_root / "src" / "config.py"),
                        "old_string": "with open('/config/settings.json') as f:",
                        "new_string": "try:\\n    with open('/config/settings.json') as f:",
                    },
                    "result": {"success": True},
                },
                {
                    "timestamp": "2025-01-27T14:02:00Z",
                    "type": "tool_call",
                    "tool": "Edit",
                    "parameters": {
                        "file_path": str(project_root / "src" / "config.py"),
                        "old_string": "        config = json.load(f)",
                        "new_string": "        config = json.load(f)\\nexcept FileNotFoundError:\\n    config = {}",
                    },
                    "result": {"success": True},
                },
            ]

            with open(session2_file, "w") as f:
                for entry in session2_entries:
                    json.dump(entry, f)
                    f.write("\\n")

            # Session 3: Testing improvements
            session3_dir = project_root / "tests" / ".claude-trace"
            session3_dir.mkdir()
            session3_file = session3_dir / "session_20250127_160000.jsonl"

            session3_entries = [
                {
                    "timestamp": "2025-01-27T16:00:00Z",
                    "type": "tool_call",
                    "tool": "Bash",
                    "parameters": {"command": "pytest tests/ -v"},
                    "result": {
                        "success": False,
                        "stdout": "FAILED tests/test_main.py::test_process_items - AssertionError",
                        "returncode": 1,
                    },
                },
                {
                    "timestamp": "2025-01-27T16:01:00Z",
                    "type": "tool_call",
                    "tool": "Edit",
                    "parameters": {
                        "file_path": str(project_root / "tests" / "test_main.py"),
                        "old_string": "assert result == expected",
                        "new_string": "assert result == expected, f'Expected {expected}, got {result}'",
                    },
                    "result": {"success": True},
                },
            ]

            with open(session3_file, "w") as f:
                for entry in session3_entries:
                    json.dump(entry, f)
                    f.write("\\n")

            yield project_root

    def test_end_to_end_workflow_with_issue_creation(
        self, mock_github_environment, sample_project_structure
    ):
        """Test complete workflow: discover traces -> analyze -> create issues."""
        project_root = sample_project_structure

        # Mock GitHub issue creation
        with patch("amplihack.tools.github_issue.create_issue") as mock_create_issue:
            mock_create_issue.side_effect = [
                {
                    "success": True,
                    "issue_number": 200,
                    "issue_url": "https://github.com/test/repo/issues/200",
                },
                {
                    "success": True,
                    "issue_number": 201,
                    "issue_url": "https://github.com/test/repo/issues/201",
                },
                {
                    "success": True,
                    "issue_number": 202,
                    "issue_url": "https://github.com/test/repo/issues/202",
                },
            ]

            # Mock existing issues check (no duplicates)
            with patch("subprocess.run") as mock_gh_run:
                mock_gh_run.return_value = Mock(
                    returncode=0,
                    stdout="[]",  # No existing issues
                    stderr="",
                )

                # Run complete analysis
                analyzer = ClaudeTraceLogAnalyzer()
                result = analyzer.analyze_directory_tree(project_root)

                # Verify analysis results
                assert result.total_entries >= 8  # All entries from 3 sessions
                assert len(result.files_analyzed) == 3  # 3 trace files
                assert len(result.patterns) >= 2  # Should find multiple patterns

                # Verify GitHub issues were created
                assert mock_create_issue.call_count >= 2

                # Verify issue content quality
                issue_calls = mock_create_issue.call_args_list
                titles = [call.kwargs["title"] for call in issue_calls]
                bodies = [call.kwargs["body"] for call in issue_calls]

                # Should have issues for different categories
                categories = set()
                for title in titles:
                    if "Code Quality" in title:
                        categories.add("code_quality")
                    elif "Error Handling" in title:
                        categories.add("error_handling")
                    elif "Testing" in title:
                        categories.add("testing")

                assert len(categories) >= 2

                # Each issue should have proper evidence and recommendations
                for body in bodies:
                    assert "Evidence:" in body or "evidence" in body.lower()
                    assert "Recommendation:" in body or "recommendation" in body.lower()
                    assert "Files affected:" in body or "files" in body.lower()

    def test_workflow_with_duplicate_detection(
        self, mock_github_environment, sample_project_structure
    ):
        """Test workflow with existing similar issues (deduplication)."""
        project_root = sample_project_structure

        # Mock existing issues that might be duplicates
        existing_issues = [
            {
                "number": 150,
                "title": "Code Quality: Improve Python iteration patterns",
                "body": "Replace range(len()) with enumerate for better code quality",
                "state": "open",
            },
            {
                "number": 151,
                "title": "Error Handling: Add file operation safety checks",
                "body": "Wrap file operations in try-except blocks",
                "state": "open",
            },
        ]

        with patch("subprocess.run") as mock_gh_run:
            mock_gh_run.return_value = Mock(
                returncode=0, stdout=json.dumps(existing_issues), stderr=""
            )

            with patch("amplihack.tools.github_issue.create_issue") as mock_create_issue:
                mock_create_issue.return_value = {
                    "success": True,
                    "issue_number": 203,
                    "issue_url": "https://github.com/test/repo/issues/203",
                }

                analyzer = ClaudeTraceLogAnalyzer()
                result = analyzer.analyze_directory_tree(project_root)

                # Should find patterns but create fewer issues due to deduplication
                assert len(result.patterns) >= 2
                # Some issues should be skipped as duplicates
                assert mock_create_issue.call_count <= len(result.patterns)

    def test_workflow_with_github_rate_limiting(
        self, mock_github_environment, sample_project_structure
    ):
        """Test workflow handling GitHub API rate limiting."""
        project_root = sample_project_structure

        with patch("amplihack.tools.github_issue.create_issue") as mock_create_issue:
            # First call succeeds, second hits rate limit, third succeeds
            mock_create_issue.side_effect = [
                {
                    "success": True,
                    "issue_number": 204,
                    "issue_url": "https://github.com/test/repo/issues/204",
                },
                {"success": False, "error": "API rate limit exceeded. Try again later."},
                {
                    "success": True,
                    "issue_number": 205,
                    "issue_url": "https://github.com/test/repo/issues/205",
                },
            ]

            analyzer = ClaudeTraceLogAnalyzer()
            result = analyzer.analyze_directory_tree(project_root)

            # Should handle rate limiting gracefully
            assert result.total_entries > 0
            assert len(result.patterns) >= 2

            # Some issues should succeed, some should fail with rate limiting
            assert mock_create_issue.call_count >= 2

    def test_workflow_with_no_trace_files(self):
        """Test workflow with directory containing no trace files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create project structure but no .claude-trace directories
            (project_root / "src").mkdir()
            (project_root / "tests").mkdir()
            (project_root / "src" / "main.py").write_text("print('hello')")

            analyzer = ClaudeTraceLogAnalyzer()
            result = analyzer.analyze_directory_tree(project_root)

            # Should handle gracefully with no findings
            assert result.total_entries == 0
            assert len(result.files_analyzed) == 0
            assert len(result.patterns) == 0

    def test_workflow_performance_with_large_project(self, mock_github_environment):
        """Test workflow performance with large project structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create large project structure with multiple trace directories
            num_sessions = 5
            entries_per_session = 100

            for session_idx in range(num_sessions):
                session_dir = project_root / f"module_{session_idx}" / ".claude-trace"
                session_dir.mkdir(parents=True)
                session_file = session_dir / f"session_{session_idx}.jsonl"

                entries = []
                for entry_idx in range(entries_per_session):
                    entry = {
                        "timestamp": f"2025-01-27T{session_idx:02d}:{entry_idx % 60:02d}:00Z",
                        "type": "tool_call",
                        "tool": "Edit" if entry_idx % 2 == 0 else "Read",
                        "parameters": {
                            "file_path": f"/module_{session_idx}/file_{entry_idx % 10}.py"
                        },
                        "result": {"success": True},
                    }
                    entries.append(entry)

                with open(session_file, "w") as f:
                    for entry in entries:
                        json.dump(entry, f)
                        f.write("\\n")

            # Mock GitHub operations to focus on analysis performance
            with patch("amplihack.tools.github_issue.create_issue") as mock_create:
                mock_create.return_value = {"success": True, "issue_number": 300}

                start_time = datetime.now()
                analyzer = ClaudeTraceLogAnalyzer()
                result = analyzer.analyze_directory_tree(project_root)
                end_time = datetime.now()

                processing_time = (end_time - start_time).total_seconds()

                # Should process large dataset efficiently
                assert processing_time < 30.0  # 30 seconds max for 500 entries
                assert result.total_entries == num_sessions * entries_per_session
                assert len(result.files_analyzed) == num_sessions

    def test_workflow_integration_with_ci_cd(self, mock_github_environment):
        """Test workflow integration with CI/CD pipeline context."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Simulate CI/CD environment variables
            ci_env = {
                "CI": "true",
                "GITHUB_ACTIONS": "true",
                "GITHUB_REF": "refs/heads/feature/new-feature",
                "GITHUB_SHA": "abc123def456",  # pragma: allowlist secret
                "GITHUB_REPOSITORY": "test-org/test-repo",
            }

            # Create trace file with CI-related entries
            trace_dir = project_root / ".claude-trace"
            trace_dir.mkdir()
            trace_file = trace_dir / "ci_session.jsonl"

            ci_entries = [
                {
                    "timestamp": "2025-01-27T12:00:00Z",
                    "type": "tool_call",
                    "tool": "Bash",
                    "parameters": {"command": "pytest --cov=src tests/"},
                    "result": {"success": True, "stdout": "Coverage: 85%", "returncode": 0},
                    "context": {"ci_environment": True, "branch": "feature/new-feature"},
                },
                {
                    "timestamp": "2025-01-27T12:01:00Z",
                    "type": "tool_call",
                    "tool": "Edit",
                    "parameters": {
                        "file_path": "/src/untested_module.py",
                        "old_string": "def complex_function():",
                        "new_string": "def complex_function():\\n    # TODO: Add unit tests",
                    },
                    "result": {"success": True},
                },
            ]

            with open(trace_file, "w") as f:
                for entry in ci_entries:
                    json.dump(entry, f)
                    f.write("\\n")

            with patch.dict(os.environ, ci_env):
                with patch("amplihack.tools.github_issue.create_issue") as mock_create:
                    mock_create.return_value = {
                        "success": True,
                        "issue_number": 400,
                        "issue_url": "https://github.com/test-org/test-repo/issues/400",
                    }

                    analyzer = ClaudeTraceLogAnalyzer()
                    result = analyzer.analyze_directory_tree(project_root)

                    # Should include CI context in analysis
                    assert result.total_entries >= 2

                    # GitHub issues should reference CI context
                    if mock_create.call_count > 0:
                        issue_call = mock_create.call_args_list[0]
                        issue_body = issue_call.kwargs["body"]
                        # Should mention CI context or branch
                        assert (
                            "feature/new-feature" in issue_body
                            or "ci" in issue_body.lower()
                            or "automated" in issue_body.lower()
                        )

    def test_workflow_error_recovery(self, mock_github_environment, sample_project_structure):
        """Test workflow recovery from various error conditions."""
        project_root = sample_project_structure

        # Test recovery from GitHub authentication failure
        with patch("subprocess.run") as mock_gh_run:
            # First call (auth check) fails, but process continues
            mock_gh_run.side_effect = [
                Mock(returncode=1, stderr="Error: authentication failed"),  # Auth check fails
                Mock(returncode=0, stdout="[]", stderr=""),  # Subsequent calls succeed
            ]

            with patch("amplihack.tools.github_issue.create_issue") as mock_create:
                mock_create.return_value = {"success": False, "error": "Authentication required"}

                analyzer = ClaudeTraceLogAnalyzer()
                result = analyzer.analyze_directory_tree(project_root)

                # Should still complete analysis even if GitHub operations fail
                assert result.total_entries > 0
                assert len(result.patterns) >= 0
                # Error should be logged but not crash the analysis

    def test_workflow_output_validation(self, mock_github_environment, sample_project_structure):
        """Test that workflow produces valid, actionable output."""
        project_root = sample_project_structure

        with patch("amplihack.tools.github_issue.create_issue") as mock_create:
            mock_create.return_value = {
                "success": True,
                "issue_number": 500,
                "issue_url": "https://github.com/test/repo/issues/500",
            }

            analyzer = ClaudeTraceLogAnalyzer()
            result = analyzer.analyze_directory_tree(project_root)

            # Validate analysis result structure
            assert hasattr(result, "total_entries")
            assert hasattr(result, "patterns")
            assert hasattr(result, "processing_time")
            assert hasattr(result, "files_analyzed")
            assert hasattr(result, "analysis_timestamp")

            # Validate patterns are actionable
            for pattern in result.patterns:
                assert pattern.category in [
                    "code_quality",
                    "error_handling",
                    "workflow_efficiency",
                    "testing",
                    "performance",
                ]
                assert len(pattern.description) > 10  # Meaningful description
                assert len(pattern.evidence) > 0  # Has evidence
                assert len(pattern.recommendation) > 10  # Actionable recommendation
                assert 0.0 <= pattern.confidence <= 1.0  # Valid confidence score
                assert len(pattern.files_affected) > 0  # Identifies affected files

            # Validate GitHub issues were well-formed
            if mock_create.call_count > 0:
                for call in mock_create.call_args_list:
                    kwargs = call.kwargs
                    assert len(kwargs["title"]) > 5  # Meaningful title
                    assert len(kwargs["body"]) > 50  # Substantial body
                    assert "labels" in kwargs  # Has appropriate labels

                    # Should include key sections in issue body
                    body = kwargs["body"]
                    assert any(
                        keyword in body.lower()
                        for keyword in ["evidence", "recommendation", "files"]
                    )
