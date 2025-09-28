"""
Test data fixtures and mock strategies for Claude-trace log analyzer tests.

Provides realistic sample data and consistent mocking patterns.
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import Mock


class ClaudeTraceTestData:
    """Generator for realistic Claude-trace test data."""

    @staticmethod
    def create_code_improvement_session() -> List[Dict[str, Any]]:
        """Generate trace entries showing code quality improvements."""
        base_time = datetime(2025, 1, 27, 10, 0, 0, tzinfo=timezone.utc)

        return [
            {
                "timestamp": base_time.isoformat(),
                "type": "tool_call",
                "tool": "Read",
                "parameters": {"file_path": "/src/utils.py"},
                "result": {
                    "success": True,
                    "content": """def process_data(items):
    # Inefficient patterns
    for i in range(len(items)):
        if items[i] == True:
            result = items[i]
    return result""",
                },
            },
            {
                "timestamp": (base_time + timedelta(minutes=1)).isoformat(),
                "type": "tool_call",
                "tool": "Edit",
                "parameters": {
                    "file_path": "/src/utils.py",
                    "old_string": "for i in range(len(items)):",
                    "new_string": "for i, item in enumerate(items):",
                },
                "result": {"success": True},
            },
            {
                "timestamp": (base_time + timedelta(minutes=2)).isoformat(),
                "type": "tool_call",
                "tool": "Edit",
                "parameters": {
                    "file_path": "/src/utils.py",
                    "old_string": "if items[i] == True:",
                    "new_string": "if item:",
                },
                "result": {"success": True},
            },
            {
                "timestamp": (base_time + timedelta(minutes=3)).isoformat(),
                "type": "tool_call",
                "tool": "Edit",
                "parameters": {
                    "file_path": "/src/utils.py",
                    "old_string": "result = items[i]",
                    "new_string": "result = item",
                },
                "result": {"success": True},
            },
        ]

    @staticmethod
    def create_error_handling_session() -> List[Dict[str, Any]]:
        """Generate trace entries showing error handling improvements."""
        base_time = datetime(2025, 1, 27, 14, 0, 0, tzinfo=timezone.utc)

        return [
            {
                "timestamp": base_time.isoformat(),
                "type": "error",
                "error_type": "FileNotFoundError",
                "message": "No such file or directory: '/config/database.json'",
                "context": {
                    "tool": "Read",
                    "file_path": "/config/database.json",
                    "line_number": 12,
                    "function": "load_config",
                },
            },
            {
                "timestamp": (base_time + timedelta(minutes=1)).isoformat(),
                "type": "tool_call",
                "tool": "Edit",
                "parameters": {
                    "file_path": "/src/config.py",
                    "old_string": "with open('/config/database.json') as f:",
                    "new_string": "try:\\n    with open('/config/database.json') as f:",
                },
                "result": {"success": True},
            },
            {
                "timestamp": (base_time + timedelta(minutes=2)).isoformat(),
                "type": "tool_call",
                "tool": "Edit",
                "parameters": {
                    "file_path": "/src/config.py",
                    "old_string": "    config = json.load(f)",
                    "new_string": "    config = json.load(f)\\nexcept FileNotFoundError:\\n    config = get_default_config()",
                },
                "result": {"success": True},
            },
            {
                "timestamp": (base_time + timedelta(minutes=3)).isoformat(),
                "type": "error",
                "error_type": "AttributeError",
                "message": "'NoneType' object has no attribute 'split'",
                "context": {"tool": "Edit", "file_path": "/src/parser.py", "line_number": 45},
            },
            {
                "timestamp": (base_time + timedelta(minutes=4)).isoformat(),
                "type": "tool_call",
                "tool": "Edit",
                "parameters": {
                    "file_path": "/src/parser.py",
                    "old_string": "result.split(',')",
                    "new_string": "result.split(',') if result else []",
                },
                "result": {"success": True},
            },
        ]

    @staticmethod
    def create_workflow_inefficiency_session() -> List[Dict[str, Any]]:
        """Generate trace entries showing workflow inefficiencies."""
        base_time = datetime(2025, 1, 27, 16, 0, 0, tzinfo=timezone.utc)

        return [
            # Repeated file reads
            {
                "timestamp": base_time.isoformat(),
                "type": "tool_call",
                "tool": "Read",
                "parameters": {"file_path": "/src/main.py"},
                "result": {"success": True, "content": "def main(): pass"},
            },
            {
                "timestamp": (base_time + timedelta(seconds=30)).isoformat(),
                "type": "tool_call",
                "tool": "Read",
                "parameters": {"file_path": "/src/main.py"},
                "result": {"success": True, "content": "def main(): pass"},
            },
            {
                "timestamp": (base_time + timedelta(minutes=1)).isoformat(),
                "type": "tool_call",
                "tool": "Read",
                "parameters": {"file_path": "/src/main.py"},
                "result": {"success": True, "content": "def main(): pass"},
            },
            # Finally make an edit
            {
                "timestamp": (base_time + timedelta(minutes=2)).isoformat(),
                "type": "tool_call",
                "tool": "Edit",
                "parameters": {
                    "file_path": "/src/main.py",
                    "old_string": "def main(): pass",
                    "new_string": "def main():\\n    print('Hello World')",
                },
                "result": {"success": True},
            },
            # Inefficient testing pattern
            {
                "timestamp": (base_time + timedelta(minutes=3)).isoformat(),
                "type": "tool_call",
                "tool": "Bash",
                "parameters": {"command": "python -m pytest tests/test_main.py::test_one -v"},
                "result": {"success": True, "stdout": "PASSED", "returncode": 0},
            },
            {
                "timestamp": (base_time + timedelta(minutes=4)).isoformat(),
                "type": "tool_call",
                "tool": "Bash",
                "parameters": {"command": "python -m pytest tests/test_main.py::test_two -v"},
                "result": {"success": True, "stdout": "PASSED", "returncode": 0},
            },
            {
                "timestamp": (base_time + timedelta(minutes=5)).isoformat(),
                "type": "tool_call",
                "tool": "Bash",
                "parameters": {"command": "python -m pytest tests/test_main.py::test_three -v"},
                "result": {"success": True, "stdout": "PASSED", "returncode": 0},
            },
        ]

    @staticmethod
    def create_performance_issues_session() -> List[Dict[str, Any]]:
        """Generate trace entries showing performance issues."""
        base_time = datetime(2025, 1, 27, 18, 0, 0, tzinfo=timezone.utc)

        return [
            # High token usage
            {
                "timestamp": base_time.isoformat(),
                "type": "completion",
                "model": "claude-3-5-sonnet",
                "prompt_tokens": 8500,
                "completion_tokens": 150,
                "total_tokens": 8650,
                "context": {"task": "code_review", "file_count": 1},
            },
            {
                "timestamp": (base_time + timedelta(minutes=1)).isoformat(),
                "type": "completion",
                "model": "claude-3-5-sonnet",
                "prompt_tokens": 9200,
                "completion_tokens": 100,
                "total_tokens": 9300,
                "context": {"task": "code_generation", "file_count": 1},
            },
            # Slow operations
            {
                "timestamp": (base_time + timedelta(minutes=2)).isoformat(),
                "type": "tool_call",
                "tool": "Bash",
                "parameters": {"command": "find . -name '*.py' -exec grep -l 'TODO' {} \\;"},
                "result": {"success": True, "stdout": "500 files found", "execution_time": 45.2},
            },
            # Memory-intensive operations
            {
                "timestamp": (base_time + timedelta(minutes=3)).isoformat(),
                "type": "tool_call",
                "tool": "Read",
                "parameters": {"file_path": "/data/large_dataset.json"},
                "result": {
                    "success": True,
                    "content": "[Large JSON content]",
                    "file_size": 50000000,  # 50MB
                    "memory_usage": "200MB",
                },
            },
        ]

    @staticmethod
    def create_testing_improvements_session() -> List[Dict[str, Any]]:
        """Generate trace entries showing testing improvements."""
        base_time = datetime(2025, 1, 27, 20, 0, 0, tzinfo=timezone.utc)

        return [
            # Test failures
            {
                "timestamp": base_time.isoformat(),
                "type": "tool_call",
                "tool": "Bash",
                "parameters": {"command": "pytest tests/ -v"},
                "result": {
                    "success": False,
                    "stdout": "FAILED tests/test_utils.py::test_process_data - AssertionError: Expected 5, got 3",
                    "stderr": "",
                    "returncode": 1,
                },
            },
            # Improving test assertions
            {
                "timestamp": (base_time + timedelta(minutes=1)).isoformat(),
                "type": "tool_call",
                "tool": "Edit",
                "parameters": {
                    "file_path": "/tests/test_utils.py",
                    "old_string": "assert result == 5",
                    "new_string": "assert result == 5, f'Expected 5, got {result}'",
                },
                "result": {"success": True},
            },
            # Adding missing tests
            {
                "timestamp": (base_time + timedelta(minutes=2)).isoformat(),
                "type": "tool_call",
                "tool": "Edit",
                "parameters": {
                    "file_path": "/tests/test_utils.py",
                    "old_string": "# TODO: Add edge case tests",
                    "new_string": """def test_empty_input():
    assert process_data([]) == []

def test_none_input():
    assert process_data(None) == []""",
                },
                "result": {"success": True},
            },
            # Coverage improvements
            {
                "timestamp": (base_time + timedelta(minutes=3)).isoformat(),
                "type": "tool_call",
                "tool": "Bash",
                "parameters": {"command": "pytest --cov=src tests/"},
                "result": {"success": True, "stdout": "Coverage: 72%", "returncode": 0},
            },
        ]

    @staticmethod
    def create_malformed_entries() -> List[str]:
        """Generate malformed JSONL entries for error testing."""
        return [
            '{"timestamp": "2025-01-27T12:00:00Z", "type": "tool_call"}',  # Missing required fields
            "invalid json line",  # Not JSON
            '{"timestamp": "invalid-date", "type": "tool_call", "tool": "Read"}',  # Invalid timestamp
            "",  # Empty line
            "   ",  # Whitespace only
            '{"type": "unknown_type", "data": "test"}',  # Unknown type
            '{"timestamp": "2025-01-27T12:00:00Z", "type": null}',  # Null type
        ]

    @staticmethod
    def write_test_file(entries: List[Dict[str, Any]], file_path: Path) -> None:
        """Write test entries to a JSONL file."""
        with open(file_path, "w") as f:
            for entry in entries:
                json.dump(entry, f)
                f.write("\\n")

    @staticmethod
    def create_test_project_structure(base_dir: Path) -> Dict[str, Path]:
        """Create a realistic project structure with multiple trace directories."""
        directories = {}

        # Main project trace
        main_trace_dir = base_dir / ".claude-trace"
        main_trace_dir.mkdir(parents=True)
        directories["main"] = main_trace_dir

        # Feature development trace
        feature_trace_dir = base_dir / "feature_branch" / ".claude-trace"
        feature_trace_dir.mkdir(parents=True)
        directories["feature"] = feature_trace_dir

        # Debug session trace
        debug_trace_dir = base_dir / "debug_session" / ".claude-trace"
        debug_trace_dir.mkdir(parents=True)
        directories["debug"] = debug_trace_dir

        # Testing session trace
        test_trace_dir = base_dir / "tests" / ".claude-trace"
        test_trace_dir.mkdir(parents=True)
        directories["testing"] = test_trace_dir

        return directories


class GitHubAPIMockStrategy:
    """Mock strategies for GitHub API interactions."""

    @staticmethod
    def create_successful_issue_response(issue_number: int = 100) -> Dict[str, Any]:
        """Create a successful GitHub issue creation response."""
        return {
            "success": True,
            "issue_number": issue_number,
            "issue_url": f"https://github.com/test/repo/issues/{issue_number}",
        }

    @staticmethod
    def create_rate_limit_response() -> Dict[str, Any]:
        """Create a rate limit error response."""
        return {"success": False, "error": "API rate limit exceeded. Try again later."}

    @staticmethod
    def create_authentication_error() -> Dict[str, Any]:
        """Create an authentication error response."""
        return {"success": False, "error": "GitHub CLI is not authenticated. Run: gh auth login"}

    @staticmethod
    def create_existing_issues_response() -> List[Dict[str, Any]]:
        """Create a list of existing GitHub issues for deduplication testing."""
        return [
            {
                "number": 50,
                "title": "Code Quality: Improve Python iteration patterns",
                "body": "Replace range(len()) with enumerate for better readability",
                "state": "open",
                "labels": ["code-quality", "python"],
            },
            {
                "number": 51,
                "title": "Error Handling: Add file operation safety",
                "body": "Wrap file operations in try-except blocks to handle errors gracefully",
                "state": "open",
                "labels": ["error-handling", "robustness"],
            },
            {
                "number": 52,
                "title": "Performance: Optimize database queries",
                "body": "Add indexing and query optimization for better performance",
                "state": "closed",
                "labels": ["performance", "database"],
            },
        ]

    @staticmethod
    def mock_gh_cli_commands(command_responses: Dict[str, Any] = None) -> Mock:
        """Create mock for subprocess.run to simulate gh CLI commands."""
        if command_responses is None:
            command_responses = {
                "gh auth status": Mock(returncode=0, stdout="", stderr=""),
                "gh issue list": Mock(
                    returncode=0,
                    stdout=json.dumps(GitHubAPIMockStrategy.create_existing_issues_response()),
                    stderr="",
                ),
            }

        def side_effect(cmd, **kwargs):
            cmd_str = " ".join(cmd) if isinstance(cmd, list) else cmd
            for pattern, response in command_responses.items():
                if pattern in cmd_str:
                    return response
            # Default response
            return Mock(returncode=0, stdout="", stderr="")

        return Mock(side_effect=side_effect)


class AnalysisResultMockStrategy:
    """Mock strategies for analysis results."""

    @staticmethod
    def create_sample_patterns() -> List[Dict[str, Any]]:
        """Create sample improvement patterns for testing."""
        return [
            {
                "category": "code_quality",
                "description": "Replace range(len()) with enumerate",
                "evidence": ["for i in range(len(items)): items[i]"],
                "recommendation": "Use enumerate for better readability: for i, item in enumerate(items)",
                "confidence": 0.9,
                "files_affected": ["/src/utils.py", "/src/helpers.py"],
            },
            {
                "category": "error_handling",
                "description": "Add exception handling for file operations",
                "evidence": ["open('/path/file.txt') without try-catch"],
                "recommendation": "Wrap file operations in try-except blocks",
                "confidence": 0.85,
                "files_affected": ["/src/config.py"],
            },
            {
                "category": "workflow_efficiency",
                "description": "Reduce repeated file reads",
                "evidence": ["Read /src/main.py 3 times within 2 minutes"],
                "recommendation": "Cache file contents or batch file operations",
                "confidence": 0.75,
                "files_affected": ["/src/main.py"],
            },
            {
                "category": "testing",
                "description": "Improve test assertions",
                "evidence": ["assert result == expected without descriptive message"],
                "recommendation": "Add descriptive messages to assertions",
                "confidence": 0.8,
                "files_affected": ["/tests/test_utils.py"],
            },
        ]

    @staticmethod
    def create_performance_benchmark_data() -> Dict[str, Any]:
        """Create performance benchmark data for testing."""
        return {
            "small_dataset": {
                "entries": 100,
                "expected_time": 0.5,  # seconds
                "expected_patterns": 2,
            },
            "medium_dataset": {"entries": 1000, "expected_time": 2.0, "expected_patterns": 5},
            "large_dataset": {"entries": 10000, "expected_time": 10.0, "expected_patterns": 10},
        }


class TestDataFactory:
    """Factory for creating complete test scenarios."""

    @staticmethod
    def create_realistic_development_session(output_dir: Path) -> Dict[str, Any]:
        """Create a realistic development session with multiple improvement types."""
        session_data = {
            "metadata": {
                "session_id": "dev_session_20250127_100000",
                "duration": "2 hours",
                "focus": "feature development",
            },
            "files": {},
        }

        # Code improvement session
        code_file = output_dir / "code_improvements.jsonl"
        ClaudeTraceTestData.write_test_file(
            ClaudeTraceTestData.create_code_improvement_session(), code_file
        )
        session_data["files"]["code_improvements"] = code_file

        # Error handling session
        error_file = output_dir / "error_handling.jsonl"
        ClaudeTraceTestData.write_test_file(
            ClaudeTraceTestData.create_error_handling_session(), error_file
        )
        session_data["files"]["error_handling"] = error_file

        # Workflow session
        workflow_file = output_dir / "workflow.jsonl"
        ClaudeTraceTestData.write_test_file(
            ClaudeTraceTestData.create_workflow_inefficiency_session(), workflow_file
        )
        session_data["files"]["workflow"] = workflow_file

        return session_data

    @staticmethod
    def create_ci_cd_session(output_dir: Path) -> Dict[str, Any]:
        """Create a CI/CD automated session."""
        ci_entries = [
            {
                "timestamp": "2025-01-27T09:00:00Z",
                "type": "tool_call",
                "tool": "Bash",
                "parameters": {"command": "pytest --cov=src tests/"},
                "result": {
                    "success": True,
                    "stdout": "Coverage: 85%\\n45 tests passed",
                    "returncode": 0,
                },
                "context": {
                    "ci_environment": True,
                    "github_actions": True,
                    "branch": "main",
                    "commit": "abc123",
                },
            },
            {
                "timestamp": "2025-01-27T09:01:00Z",
                "type": "tool_call",
                "tool": "Bash",
                "parameters": {"command": "pylint src/"},
                "result": {
                    "success": False,
                    "stdout": "Your code has been rated at 7.5/10",
                    "returncode": 1,
                },
            },
        ]

        ci_file = output_dir / "ci_session.jsonl"
        ClaudeTraceTestData.write_test_file(ci_entries, ci_file)

        return {
            "metadata": {"session_type": "ci_cd", "automated": True, "branch": "main"},
            "files": {"ci_session": ci_file},
        }
