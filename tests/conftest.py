"""
Pytest configuration and fixtures for Agent Bundle Generator tests.

Provides comprehensive mocking for external dependencies (gh CLI, git, uvx)
and test data fixtures for E2E testing.
"""

import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# =============================================================================
# Mock Fixtures for External Dependencies
# =============================================================================


@pytest.fixture
def mock_gh_cli(monkeypatch):
    """
    Mock GitHub CLI operations.

    Simulates gh CLI commands for:
    - Repository creation
    - Release management
    - Repository checks
    """

    def mock_run(*args, **kwargs):
        """Mock subprocess.run for gh commands."""
        cmd = args[0] if args else kwargs.get("args", [])

        # Determine if text mode requested
        text_mode = kwargs.get("text", False)

        # gh repo create
        if "repo" in cmd and "create" in cmd:
            url = "https://github.com/testuser/test-bundle\n"
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=0,
                stdout=url if text_mode else url.encode(),
                stderr="" if text_mode else b"",
            )

        # gh repo view
        if "repo" in cmd and "view" in cmd:
            data = '{"name": "test-bundle", "url": "https://github.com/testuser/test-bundle"}\n'
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=0,
                stdout=data if text_mode else data.encode(),
                stderr="" if text_mode else b"",
            )

        # gh release create
        if "release" in cmd and "create" in cmd:
            tag = "v1.0.0\n"
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=0,
                stdout=tag if text_mode else tag.encode(),
                stderr="" if text_mode else b"",
            )

        # Default success
        return subprocess.CompletedProcess(
            args=cmd, returncode=0, stdout="" if text_mode else b"", stderr="" if text_mode else b""
        )

    monkeypatch.setattr("subprocess.run", mock_run)
    return mock_run


@pytest.fixture
def mock_git(monkeypatch):
    """
    Mock git operations.

    Simulates git commands for:
    - Repository initialization
    - Commit operations
    - Push operations
    - Status checks
    """

    def mock_run(*args, **kwargs):
        """Mock subprocess.run for git commands."""
        cmd = args[0] if args else kwargs.get("args", [])

        # Determine if text mode requested
        text_mode = kwargs.get("text", False)

        # git init
        if "init" in cmd:
            output = "Initialized empty Git repository\n"
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=0,
                stdout=output if text_mode else output.encode(),
                stderr="" if text_mode else b"",
            )

        # git add
        if "add" in cmd:
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=0,
                stdout="" if text_mode else b"",
                stderr="" if text_mode else b"",
            )

        # git commit
        if "commit" in cmd:
            output = "[main abc123] Initial commit\n"
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=0,
                stdout=output if text_mode else output.encode(),
                stderr="" if text_mode else b"",
            )

        # git push
        if "push" in cmd:
            output = "To https://github.com/testuser/test-bundle\n"
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=0,
                stdout=output if text_mode else output.encode(),
                stderr="" if text_mode else b"",
            )

        # git status
        if "status" in cmd:
            output = "On branch main\nnothing to commit\n"
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=0,
                stdout=output if text_mode else output.encode(),
                stderr="" if text_mode else b"",
            )

        # git remote
        if "remote" in cmd:
            output = "origin\thttps://github.com/testuser/test-bundle\n"
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=0,
                stdout=output if text_mode else output.encode(),
                stderr="" if text_mode else b"",
            )

        # Default success
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=0,
            stdout="" if text_mode else b"",
            stderr="" if text_mode else b"",
        )

    monkeypatch.setattr("subprocess.run", mock_run)
    return mock_run


@pytest.fixture
def mock_uvx_build(monkeypatch):
    """
    Mock UVX build process.

    Simulates:
    - Package building
    - UVX execution
    - Package validation
    """

    def mock_build(*args, **kwargs):
        """Mock Python build process."""
        # Simulate successful build
        return subprocess.CompletedProcess(
            args=["python", "-m", "build"],
            returncode=0,
            stdout=b"Successfully built test-bundle-1.0.0.tar.gz\n",
            stderr=b"",
        )

    # Mock subprocess calls for build
    original_run = subprocess.run

    def selective_mock_run(*args, **kwargs):
        cmd = args[0] if args else kwargs.get("args", [])
        if "build" in cmd or "uvx" in cmd:
            return mock_build(*args, **kwargs)
        return original_run(*args, **kwargs)

    monkeypatch.setattr("subprocess.run", selective_mock_run)
    return mock_build


@pytest.fixture
def mock_update_check(monkeypatch):
    """
    Mock framework update checks.

    Simulates:
    - Version checking
    - Update availability detection
    - Changelog retrieval
    """

    class MockUpdateInfo:
        """Mock update information."""

        def __init__(self):
            self.current_version = "1.0.0"
            self.latest_version = "1.0.0"
            self.available = False
            self.changes = []

    def mock_check(*args, **kwargs):
        """Mock update check."""
        return MockUpdateInfo()

    # Patch UpdateManager.check_for_updates
    with patch("amplihack.bundle_generator.update_manager.UpdateManager.check_for_updates") as mock:
        mock.return_value = MockUpdateInfo()
        yield mock


# =============================================================================
# Test Data Fixtures
# =============================================================================


@pytest.fixture
def temp_output_dir():
    """
    Temporary output directory for test bundles.

    Automatically cleaned up after test completion.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_prompt():
    """
    Sample prompt for bundle generation.

    Returns a simple, valid prompt for testing.
    """
    return "Create a monitoring agent that tracks API performance and sends alerts"


@pytest.fixture
def generated_bundle(temp_output_dir):
    """
    Pre-generated bundle structure for testing.

    Creates a complete bundle directory with:
    - manifest.json
    - Agent files
    - Test files
    - Documentation
    - Repackaging scripts
    """
    bundle_dir = temp_output_dir / "test-monitoring-bundle"
    bundle_dir.mkdir(parents=True)

    # Create bundle structure
    (bundle_dir / "agents").mkdir()
    (bundle_dir / "tests").mkdir()
    (bundle_dir / "docs").mkdir()

    # Create manifest
    manifest = {
        "bundle": {
            "name": "test-monitoring-bundle",
            "version": "1.0.0",
            "description": "Test monitoring bundle",
            "created_at": "2025-01-28T00:00:00",
        },
        "agents": [
            {
                "name": "monitoring-agent",
                "type": "specialized",
                "role": "Monitor API performance",
                "file": "agents/monitoring-agent.md",
            }
        ],
        "metadata": {
            "generated_by": "bundle-generator",
            "framework_version": "1.0.0",
        },
    }

    (bundle_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

    # Create agent file
    agent_content = """# Monitoring Agent

**Role:** Monitor API performance and send alerts

## Capabilities
- Track API response times
- Monitor error rates
- Send alerts on threshold breaches

## Implementation
This agent monitors API endpoints and tracks performance metrics.
"""
    (bundle_dir / "agents" / "monitoring-agent.md").write_text(agent_content)

    # Create test file
    test_content = '''"""Tests for monitoring agent."""

import pytest


def test_monitoring_agent():
    """Test monitoring agent functionality."""
    assert True  # Placeholder test
'''
    (bundle_dir / "tests" / "test_monitoring_agent.py").write_text(test_content)

    # Create INSTRUCTIONS.md
    instructions = """# Test Monitoring Bundle

## Quick Start
1. Install dependencies: `pip install -r requirements.txt`
2. Run the bundle: `python -m test_monitoring_bundle`

## Editing and Repackaging
After editing agents, run: `./repackage.sh`
"""
    (bundle_dir / "INSTRUCTIONS.md").write_text(instructions)

    # Create repackage script
    repackage_script = """#!/bin/bash
# Repackage bundle after edits

set -e
echo "Repackaging bundle..."
python -m build
echo "✅ Repackaging complete!"
"""
    repackage_path = bundle_dir / "repackage.sh"
    repackage_path.write_text(repackage_script)
    repackage_path.chmod(0o755)

    # Create pyproject.toml
    pyproject = """[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "test-monitoring-bundle"
version = "1.0.0"
description = "Test monitoring bundle"
requires-python = ">=3.11"

[project.scripts]
test-monitoring-bundle = "test_monitoring_bundle.__main__:main"
"""
    (bundle_dir / "pyproject.toml").write_text(pyproject)

    return bundle_dir


# =============================================================================
# Composite Mock Environment
# =============================================================================


@pytest.fixture
def mock_env(mock_gh_cli, mock_git, mock_uvx_build, mock_update_check):
    """
    Composite fixture with all external mocks enabled.

    Combines:
    - GitHub CLI mocking
    - Git operations mocking
    - UVX build mocking
    - Update check mocking

    Use this for complete E2E tests that need all external
    dependencies mocked.
    """
    return {
        "gh_cli": mock_gh_cli,
        "git": mock_git,
        "uvx_build": mock_uvx_build,
        "update_check": mock_update_check,
    }


# =============================================================================
# Helper Functions
# =============================================================================


@pytest.fixture
def assert_bundle_structure():
    """
    Fixture providing bundle structure validation helper.

    Returns a function that validates bundle directory structure.
    """

    def validate(bundle_path: Path, expect_repackage=True, expect_instructions=True):
        """
        Validate bundle structure.

        Args:
            bundle_path: Path to bundle directory
            expect_repackage: Whether repackage script should exist
            expect_instructions: Whether INSTRUCTIONS.md should exist
        """
        assert bundle_path.exists(), f"Bundle directory not found: {bundle_path}"
        assert (bundle_path / "manifest.json").exists(), "manifest.json not found"
        assert (bundle_path / "agents").exists(), "agents/ directory not found"

        if expect_repackage:
            repackage = bundle_path / "repackage.sh"
            assert repackage.exists(), "repackage.sh not found"
            # Check executable
            assert repackage.stat().st_mode & 0o111, "repackage.sh not executable"

        if expect_instructions:
            instructions = bundle_path / "INSTRUCTIONS.md"
            assert instructions.exists(), "INSTRUCTIONS.md not found"
            content = instructions.read_text()
            assert "Quick Start" in content or "Run" in content.lower()

        # Validate manifest structure
        manifest_data = json.loads((bundle_path / "manifest.json").read_text())
        assert "bundle" in manifest_data, "manifest missing 'bundle' section"
        assert "agents" in manifest_data, "manifest missing 'agents' section"

    return validate


@pytest.fixture
def assert_package_valid():
    """
    Fixture providing package validation helper.

    Returns a function that validates packaged bundles.
    """

    def validate(package_path: Path, expected_format="uvx"):
        """
        Validate packaged bundle.

        Args:
            package_path: Path to package file
            expected_format: Expected package format
        """
        assert package_path.exists(), f"Package not found: {package_path}"

        if expected_format == "uvx":
            # For directory-based uvx packages
            if package_path.is_dir():
                # Should have pyproject.toml for directory-based packages
                assert (package_path / "pyproject.toml").exists()
            else:
                # For archive formats including .uvx
                assert package_path.suffix in [".tar", ".gz", ".zip", ".uvx"]

        return True

    return validate


# =============================================================================
# Stop Hook Test Fixtures
# =============================================================================


@pytest.fixture
def temp_project_root(tmp_path):
    """Create temporary project structure for stop hook tests.

    Returns:
        Path: Temporary project root with .claude directory structure
    """
    project = tmp_path / "project"
    project.mkdir()

    # Create directory structure
    (project / ".claude/tools/amplihack/hooks").mkdir(parents=True)
    (project / ".claude/runtime/logs").mkdir(parents=True)
    (project / ".claude/runtime/metrics").mkdir(parents=True)

    return project


@pytest.fixture
def stop_hook(temp_project_root):
    """Create StopHook instance with test paths.

    Args:
        temp_project_root: Temporary project root fixture

    Returns:
        StopHook: Configured hook instance for testing
    """
    import sys

    # Import here to avoid circular import issues
    sys.path.insert(0, str(Path(__file__).parent.parent / ".claude/tools/amplihack/hooks"))
    from stop import StopHook

    hook = StopHook()
    hook.project_root = temp_project_root
    hook.lock_flag = temp_project_root / ".claude/tools/amplihack/.lock_active"
    hook.continuation_prompt_file = (
        temp_project_root / ".claude/tools/amplihack/.continuation_prompt"
    )
    hook.log_dir = temp_project_root / ".claude/runtime/logs"
    hook.metrics_dir = temp_project_root / ".claude/runtime/metrics"
    hook.analysis_dir = temp_project_root / ".claude/runtime/analysis"
    hook.log_file = hook.log_dir / "stop.log"

    return hook


@pytest.fixture
def active_lock(stop_hook):
    """Create active lock file.

    Args:
        stop_hook: StopHook fixture

    Yields:
        Path: Lock file path
    """
    stop_hook.lock_flag.touch()
    yield stop_hook.lock_flag
    if stop_hook.lock_flag.exists():
        stop_hook.lock_flag.unlink()


@pytest.fixture
def custom_prompt(stop_hook):
    """Create custom continuation prompt.

    Args:
        stop_hook: StopHook fixture

    Returns:
        callable: Function to create prompt with given content
    """

    def _create_prompt(content: str) -> Path:
        stop_hook.continuation_prompt_file.write_text(content, encoding="utf-8")
        return stop_hook.continuation_prompt_file

    return _create_prompt


@pytest.fixture
def captured_subprocess(temp_project_root):
    """Run hook as subprocess and capture output.

    Args:
        temp_project_root: Temporary project root fixture

    Returns:
        callable: Function to run hook subprocess
    """
    import sys
    import os

    # Path to the actual stop.py hook
    hook_script = Path(__file__).parent.parent / ".claude/tools/amplihack/hooks/stop.py"

    def _run(input_data: dict, lock_active: bool = False) -> subprocess.CompletedProcess:
        """Run hook as subprocess with input.

        Args:
            input_data: JSON input to pass to hook
            lock_active: Whether to create lock file

        Returns:
            CompletedProcess with stdout, stderr, exit code
        """
        # Setup environment - make sure directories exist
        (temp_project_root / ".claude/tools/amplihack").mkdir(parents=True, exist_ok=True)

        # Setup lock file if requested
        if lock_active:
            lock_file = temp_project_root / ".claude/tools/amplihack/.lock_active"
            lock_file.touch()

        # Prepare input
        json_input = json.dumps(input_data)

        # Set environment to point to temp project root
        env = os.environ.copy()
        env["AMPLIHACK_PROJECT_ROOT"] = str(temp_project_root)

        # Run subprocess
        result = subprocess.run(
            [sys.executable, str(hook_script)],
            input=json_input,
            capture_output=True,
            text=True,
            timeout=5,
            cwd=str(temp_project_root),
            env=env,
        )

        return result

    return _run


@pytest.fixture
def mock_time():
    """Fixture for timing tests.

    Returns:
        callable: Time tracking context manager
    """
    import time

    class TimeTracker:
        def __init__(self):
            self.start = None
            self.end = None
            self.duration_ms = None

        def __enter__(self):
            self.start = time.perf_counter()
            return self

        def __exit__(self, *args):
            self.end = time.perf_counter()
            self.duration_ms = (self.end - self.start) * 1000

    return TimeTracker
