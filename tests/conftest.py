#!/usr/bin/env python3
"""
pytest configuration and fixtures for reflection automation tests.
Provides common test fixtures and configuration.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add project to path
project_root = Path(__file__).parent.parent


@pytest.fixture
def temp_dir():
    """Provide temporary directory for tests"""
    with tempfile.TemporaryDirectory() as temp_path:
        yield Path(temp_path)


@pytest.fixture
def mock_github_api():
    """Mock GitHub API for testing"""
    from test_mocks import MockGitHubAPI

    api = MockGitHubAPI()
    yield api
    api.reset()


@pytest.fixture
def mock_github_cli():
    """Mock GitHub CLI for testing"""
    from test_mocks import MockGitHubAPI, MockGitHubCLI

    api = MockGitHubAPI()
    cli = MockGitHubCLI(api)

    with patch("subprocess.run", side_effect=cli.mock_gh_command):
        yield cli, api


@pytest.fixture
def reflection_disabled():
    """Disable reflection to prevent infinite loops in tests"""
    original_env = os.environ.get("CLAUDE_REFLECTION_MODE")
    os.environ["CLAUDE_REFLECTION_MODE"] = "1"  # Disable reflection
    yield
    if original_env is not None:
        os.environ["CLAUDE_REFLECTION_MODE"] = original_env
    else:
        os.environ.pop("CLAUDE_REFLECTION_MODE", None)


@pytest.fixture
def sample_messages():
    """Provide sample message data for testing"""
    from test_mocks import MockSessionData

    return {
        "simple": MockSessionData.create_simple_session(),
        "repeated_tools": MockSessionData.create_repeated_tool_session(),
        "errors": MockSessionData.create_error_pattern_session(),
        "frustration": MockSessionData.create_frustration_session(),
        "long": MockSessionData.create_long_session(),
        "mixed": MockSessionData.create_mixed_pattern_session(),
    }


@pytest.fixture
def automation_config(temp_dir):
    """Provide automation configuration for testing"""
    config = {
        "automation_enabled": True,
        "trigger_thresholds": {
            "min_pattern_severity": "medium",
            "min_pattern_count": 2,
            "cooldown_hours": 1,
        },
        "workflow_constraints": {
            "max_concurrent_workflows": 2,
            "max_lines_per_improvement": 200,
            "max_components_per_improvement": 3,
        },
    }

    config_file = temp_dir / "automation_config.json"
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)

    return config_file


@pytest.fixture
def claude_runtime_structure(temp_dir):
    """Create .claude runtime directory structure for testing"""
    claude_dir = temp_dir / ".claude"
    runtime_dir = claude_dir / "runtime"
    logs_dir = runtime_dir / "logs"
    queue_dir = runtime_dir / "improvement_queue"
    failed_dir = runtime_dir / "failed_workflows"

    # Create directories
    for directory in [claude_dir, runtime_dir, logs_dir, queue_dir, failed_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    return {
        "claude_dir": claude_dir,
        "runtime_dir": runtime_dir,
        "logs_dir": logs_dir,
        "queue_dir": queue_dir,
        "failed_dir": failed_dir,
    }


# Test markers
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line("markers", "unit: Unit tests for individual components")
    config.addinivalue_line("markers", "integration: Integration tests for component interaction")
    config.addinivalue_line("markers", "safety: Safety mechanism tests")
    config.addinivalue_line("markers", "slow: Slow-running tests")
    config.addinivalue_line("markers", "github: Tests requiring GitHub API simulation")


# Skip tests if dependencies not available
def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle missing dependencies"""
    skip_github = pytest.mark.skip(reason="GitHub integration not available")

    for item in items:
        if "github" in item.keywords:
            # Could add logic to skip if GitHub CLI not available
            pass
