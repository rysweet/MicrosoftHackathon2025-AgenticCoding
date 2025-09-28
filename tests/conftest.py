"""
Pytest configuration and shared fixtures for Claude-trace log analyzer tests.

Provides test configuration, shared fixtures, and utilities for comprehensive testing.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from tests.fixtures.claude_trace_test_data import (
    ClaudeTraceTestData,
    GitHubAPIMockStrategy,
    TestDataFactory,
)

# Test configuration
pytest_plugins = ["fixtures.claude_trace_test_data"]


@pytest.fixture(scope="session")
def test_data_factory():
    """Provide test data factory for creating realistic test scenarios."""
    return TestDataFactory


@pytest.fixture(scope="function")
def temp_directory():
    """Provide temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture(scope="function")
def sample_trace_files(temp_directory):
    """Create sample trace files for testing."""
    trace_files = {}

    # Code improvement session
    code_file = temp_directory / "code_session.jsonl"
    ClaudeTraceTestData.write_test_file(
        ClaudeTraceTestData.create_code_improvement_session(), code_file
    )
    trace_files["code_improvements"] = code_file

    # Error handling session
    error_file = temp_directory / "error_session.jsonl"
    ClaudeTraceTestData.write_test_file(
        ClaudeTraceTestData.create_error_handling_session(), error_file
    )
    trace_files["error_handling"] = error_file

    # Workflow session
    workflow_file = temp_directory / "workflow_session.jsonl"
    ClaudeTraceTestData.write_test_file(
        ClaudeTraceTestData.create_workflow_inefficiency_session(), workflow_file
    )
    trace_files["workflow"] = workflow_file

    return trace_files


@pytest.fixture(scope="function")
def mock_github_success():
    """Mock successful GitHub operations."""
    with patch("amplihack.tools.github_issue.create_issue") as mock_create:
        mock_create.return_value = GitHubAPIMockStrategy.create_successful_issue_response()

        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.return_value = Mock(
                returncode=0,
                stdout=json.dumps(GitHubAPIMockStrategy.create_existing_issues_response()),
                stderr="",
            )
            yield {"create_issue": mock_create, "subprocess": mock_subprocess}


@pytest.fixture(scope="function")
def mock_github_rate_limited():
    """Mock GitHub rate limiting scenario."""
    with patch("amplihack.tools.github_issue.create_issue") as mock_create:
        mock_create.return_value = GitHubAPIMockStrategy.create_rate_limit_response()
        yield mock_create


@pytest.fixture(scope="function")
def project_with_traces(temp_directory):
    """Create a realistic project structure with multiple trace directories."""
    project_root = temp_directory

    # Create project structure
    (project_root / "src").mkdir()
    (project_root / "tests").mkdir()
    (project_root / "docs").mkdir()

    # Create trace directories
    trace_dirs = ClaudeTraceTestData.create_test_project_structure(project_root)

    # Populate with test data
    ClaudeTraceTestData.write_test_file(
        ClaudeTraceTestData.create_code_improvement_session(), trace_dirs["main"] / "session1.jsonl"
    )

    ClaudeTraceTestData.write_test_file(
        ClaudeTraceTestData.create_error_handling_session(),
        trace_dirs["feature"] / "session2.jsonl",
    )

    ClaudeTraceTestData.write_test_file(
        ClaudeTraceTestData.create_testing_improvements_session(),
        trace_dirs["testing"] / "session3.jsonl",
    )

    return {"root": project_root, "trace_dirs": trace_dirs}


@pytest.fixture(scope="function")
def performance_test_data(temp_directory):
    """Create performance test data of various sizes."""
    performance_files = {}

    sizes = [100, 1000, 5000]
    for size in sizes:
        entries = []
        for i in range(size):
            entry = {
                "timestamp": f"2025-01-27T{i // 3600:02d}:{(i % 3600) // 60:02d}:{i % 60:02d}Z",
                "type": "tool_call",
                "tool": "Edit" if i % 2 == 0 else "Read",
                "parameters": {"file_path": f"/file_{i % 10}.py"},
                "result": {"success": True},
            }
            entries.append(entry)

        perf_file = temp_directory / f"perf_{size}_entries.jsonl"
        ClaudeTraceTestData.write_test_file(entries, perf_file)
        performance_files[size] = perf_file

    return performance_files


# Test markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: mark test as unit test (fast, isolated)")
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (components working together)"
    )
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test (full workflow)")
    config.addinivalue_line("markers", "performance: mark test as performance test (may be slow)")
    config.addinivalue_line("markers", "error_case: mark test as error handling test")
    config.addinivalue_line("markers", "slow: mark test as slow (may take several seconds)")


# Custom test collection
def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on file names and patterns."""
    for item in items:
        # Mark tests based on file name
        if "unit" in item.fspath.basename:
            item.add_marker(pytest.mark.unit)
        elif "integration" in item.fspath.basename:
            item.add_marker(pytest.mark.integration)
        elif "e2e" in item.fspath.basename:
            item.add_marker(pytest.mark.e2e)
        elif "performance" in item.fspath.basename:
            item.add_marker(pytest.mark.performance)

        # Mark performance tests as slow
        if "performance" in item.name.lower() or "large" in item.name.lower():
            item.add_marker(pytest.mark.slow)

        # Mark error handling tests
        if "error" in item.name.lower() or "failure" in item.name.lower():
            item.add_marker(pytest.mark.error_case)


# Test utilities
class TestUtils:
    """Utility functions for tests."""

    @staticmethod
    def assert_valid_improvement_pattern(pattern):
        """Assert that an improvement pattern has all required fields and valid values."""
        required_fields = [
            "category",
            "description",
            "evidence",
            "recommendation",
            "confidence",
            "files_affected",
        ]

        for field in required_fields:
            assert hasattr(pattern, field), f"Pattern missing required field: {field}"

        # Validate field types and constraints
        assert isinstance(pattern.category, str) and len(pattern.category) > 0
        assert isinstance(pattern.description, str) and len(pattern.description) > 10
        assert isinstance(pattern.evidence, list) and len(pattern.evidence) > 0
        assert isinstance(pattern.recommendation, str) and len(pattern.recommendation) > 10
        assert isinstance(pattern.confidence, (int, float)) and 0.0 <= pattern.confidence <= 1.0
        assert isinstance(pattern.files_affected, list)

    @staticmethod
    def assert_valid_analysis_result(result):
        """Assert that an analysis result has all required fields and valid values."""
        required_fields = [
            "total_entries",
            "patterns",
            "processing_time",
            "files_analyzed",
            "analysis_timestamp",
        ]

        for field in required_fields:
            assert hasattr(result, field), f"Result missing required field: {field}"

        # Validate field types and constraints
        assert isinstance(result.total_entries, int) and result.total_entries >= 0
        assert isinstance(result.patterns, list)
        assert isinstance(result.processing_time, (int, float)) and result.processing_time >= 0
        assert isinstance(result.files_analyzed, list)

        # Validate patterns
        for pattern in result.patterns:
            TestUtils.assert_valid_improvement_pattern(pattern)

    @staticmethod
    def count_patterns_by_category(patterns):
        """Count patterns by category for test assertions."""
        category_counts = {}
        for pattern in patterns:
            category = pattern.category
            category_counts[category] = category_counts.get(category, 0) + 1
        return category_counts


@pytest.fixture(scope="function")
def test_utils():
    """Provide test utilities."""
    return TestUtils
