#!/usr/bin/env python3
"""
Mock infrastructure for GitHub API and session data testing.
Provides realistic mock data and GitHub API simulation for testing.
"""

import json
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import pytest

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class MockGitHubAPI:
    """Mock GitHub API for testing without actual API calls"""

    def __init__(self):
        self.issues = {}
        self.prs = {}
        self.next_issue_id = 1
        self.next_pr_id = 1
        self.api_calls = []
        self.rate_limit_remaining = 5000
        self.should_fail = False
        self.failure_type = None

    def create_issue(self, title: str, body: str, labels: List[str] = None) -> Dict:
        """Mock issue creation"""
        self.api_calls.append(
            {
                "action": "create_issue",
                "title": title,
                "body": body,
                "labels": labels or [],
                "timestamp": datetime.now().isoformat(),
            }
        )

        if self.should_fail:
            if self.failure_type == "rate_limit":
                raise Exception("API rate limit exceeded")
            elif self.failure_type == "auth":
                raise Exception("Authentication failed")
            elif self.failure_type == "network":
                raise Exception("Network error")
            else:
                raise Exception("Unknown API error")

        issue_id = self.next_issue_id
        self.next_issue_id += 1

        issue = {
            "id": issue_id,
            "number": issue_id,
            "title": title,
            "body": body,
            "labels": labels or [],
            "state": "open",
            "created_at": datetime.now().isoformat(),
            "url": f"https://github.com/test/repo/issues/{issue_id}",
        }

        self.issues[issue_id] = issue
        self.rate_limit_remaining -= 1

        return issue

    def create_pr(self, title: str, body: str, base: str = "main", head: str = "feature") -> Dict:
        """Mock PR creation"""
        self.api_calls.append(
            {
                "action": "create_pr",
                "title": title,
                "body": body,
                "base": base,
                "head": head,
                "timestamp": datetime.now().isoformat(),
            }
        )

        if self.should_fail:
            raise Exception(f"PR creation failed: {self.failure_type}")

        pr_id = self.next_pr_id
        self.next_pr_id += 1

        pr = {
            "id": pr_id,
            "number": pr_id,
            "title": title,
            "body": body,
            "base": {"ref": base},
            "head": {"ref": head},
            "state": "open",
            "created_at": datetime.now().isoformat(),
            "url": f"https://github.com/test/repo/pull/{pr_id}",
        }

        self.prs[pr_id] = pr
        self.rate_limit_remaining -= 1

        return pr

    def set_failure_mode(self, should_fail: bool, failure_type: str = "generic"):
        """Configure API to simulate failures"""
        self.should_fail = should_fail
        self.failure_type = failure_type

    def get_api_calls(self) -> List[Dict]:
        """Get history of API calls for testing"""
        return self.api_calls.copy()

    def reset(self):
        """Reset mock state"""
        self.issues.clear()
        self.prs.clear()
        self.api_calls.clear()
        self.next_issue_id = 1
        self.next_pr_id = 1
        self.rate_limit_remaining = 5000
        self.should_fail = False
        self.failure_type = None


class MockGitHubCLI:
    """Mock GitHub CLI for testing subprocess calls"""

    def __init__(self, mock_github_api: MockGitHubAPI):
        self.api = mock_github_api
        self.should_fail = False
        self.failure_type = None

    def mock_gh_command(self, cmd: List[str], **kwargs) -> subprocess.CompletedProcess:
        """Mock gh CLI commands"""
        if self.should_fail:
            if self.failure_type == "not_found":
                return subprocess.CompletedProcess(
                    args=cmd, returncode=127, stdout="", stderr="gh: command not found"
                )
            elif self.failure_type == "auth":
                return subprocess.CompletedProcess(
                    args=cmd, returncode=1, stdout="", stderr="gh: authentication failed"
                )
            else:
                return subprocess.CompletedProcess(
                    args=cmd, returncode=1, stdout="", stderr="gh: unknown error"
                )

        # Parse command
        if len(cmd) < 3:
            return subprocess.CompletedProcess(
                args=cmd, returncode=1, stdout="", stderr="Invalid command"
            )

        if cmd[1] == "issue" and cmd[2] == "create":
            # Extract issue details from command
            title = ""
            body = ""
            labels = []

            for i, arg in enumerate(cmd):
                if arg == "--title" and i + 1 < len(cmd):
                    title = cmd[i + 1]
                elif arg == "--body" and i + 1 < len(cmd):
                    body = cmd[i + 1]
                elif arg == "--label" and i + 1 < len(cmd):
                    labels.append(cmd[i + 1])

            try:
                issue = self.api.create_issue(title, body, labels)
                return subprocess.CompletedProcess(
                    args=cmd, returncode=0, stdout=issue["url"], stderr=""
                )
            except Exception as e:
                return subprocess.CompletedProcess(args=cmd, returncode=1, stdout="", stderr=str(e))

        elif cmd[1] == "pr" and cmd[2] == "create":
            # Extract PR details
            title = ""
            body = ""
            base = "main"
            head = "feature"

            for i, arg in enumerate(cmd):
                if arg == "--title" and i + 1 < len(cmd):
                    title = cmd[i + 1]
                elif arg == "--body" and i + 1 < len(cmd):
                    body = cmd[i + 1]
                elif arg == "--base" and i + 1 < len(cmd):
                    base = cmd[i + 1]
                elif arg == "--head" and i + 1 < len(cmd):
                    head = cmd[i + 1]

            try:
                pr = self.api.create_pr(title, body, base, head)
                return subprocess.CompletedProcess(
                    args=cmd, returncode=0, stdout=pr["url"], stderr=""
                )
            except Exception as e:
                return subprocess.CompletedProcess(args=cmd, returncode=1, stdout="", stderr=str(e))

        elif cmd[1] == "--version":
            return subprocess.CompletedProcess(
                args=cmd, returncode=0, stdout="gh version 2.0.0", stderr=""
            )

        # Unknown command
        return subprocess.CompletedProcess(
            args=cmd, returncode=1, stdout="", stderr="Unknown command"
        )

    def set_failure_mode(self, should_fail: bool, failure_type: str = "generic"):
        """Configure CLI to simulate failures"""
        self.should_fail = should_fail
        self.failure_type = failure_type


class MockSessionData:
    """Generate realistic mock session data for testing"""

    @staticmethod
    def create_simple_session() -> List[Dict]:
        """Create a simple session with basic interaction"""
        return [
            {"role": "user", "content": "Hello, can you help me with a simple task?"},
            {
                "role": "assistant",
                "content": "I'd be happy to help! What do you need assistance with?",
            },
            {"role": "user", "content": "I need to check if a file exists."},
            {
                "role": "assistant",
                "content": '<function_calls><invoke name="Bash"><parameter name="command">ls -la example.txt</parameter></invoke></function_calls>',
            },
        ]

    @staticmethod
    def create_repeated_tool_session() -> List[Dict]:
        """Create session with repeated tool usage pattern"""
        messages = [
            {"role": "user", "content": "I need to process multiple files"},
            {"role": "assistant", "content": "I'll help you process the files systematically."},
        ]

        # Add repeated bash commands
        for i in range(8):
            messages.append(
                {
                    "role": "assistant",
                    "content": f'<function_calls><invoke name="Bash"><parameter name="command">process_file_{i}.py</parameter></invoke></function_calls>',
                }
            )
            messages.append(
                {"role": "user", "content": f"File {i} processed, continue with next one"}
            )

        return messages

    @staticmethod
    def create_error_pattern_session() -> List[Dict]:
        """Create session with error patterns"""
        return [
            {"role": "user", "content": "I'm having trouble with this script"},
            {"role": "assistant", "content": "Let me help you debug the script."},
            {
                "role": "assistant",
                "content": '<function_calls><invoke name="Bash"><parameter name="command">python script.py</parameter></invoke></function_calls>',
            },
            {"role": "user", "content": "Getting an error: FileNotFoundError"},
            {"role": "assistant", "content": "Let me check the file path."},
            {
                "role": "assistant",
                "content": '<function_calls><invoke name="Bash"><parameter name="command">ls -la</parameter></invoke></function_calls>',
            },
            {"role": "user", "content": "Still getting errors, this doesn't work"},
            {"role": "assistant", "content": "Let me try a different approach."},
            {"role": "user", "content": "Another error: PermissionError, this is broken"},
            {"role": "assistant", "content": "I'll check the permissions."},
            {"role": "user", "content": "Failed again with ImportError, why isn't this working?"},
        ]

    @staticmethod
    def create_frustration_session() -> List[Dict]:
        """Create session with user frustration indicators"""
        return [
            {"role": "user", "content": "I need to set up authentication"},
            {"role": "assistant", "content": "I'll help you set up authentication."},
            {"role": "user", "content": "This doesn't work as expected"},
            {"role": "assistant", "content": "Let me try a different configuration."},
            {"role": "user", "content": "Still not working, I'm getting confused"},
            {"role": "assistant", "content": "Let me simplify the approach."},
            {"role": "user", "content": "This should be simple but it's still broken"},
            {
                "role": "assistant",
                "content": "I understand your frustration. Let me debug this step by step.",
            },
            {"role": "user", "content": "I'm stuck and don't understand why this isn't working"},
            {"role": "assistant", "content": "Let me review the entire setup from the beginning."},
        ]

    @staticmethod
    def create_long_session() -> List[Dict]:
        """Create a long session with many interactions"""
        messages = [
            {"role": "user", "content": "I need to refactor a large codebase"},
            {"role": "assistant", "content": "I'll help you refactor the codebase systematically."},
        ]

        # Add many back-and-forth interactions
        for i in range(60):
            messages.extend(
                [
                    {"role": "user", "content": f"Let's work on module {i}"},
                    {
                        "role": "assistant",
                        "content": f"I'll analyze module {i} for refactoring opportunities.",
                    },
                    {
                        "role": "assistant",
                        "content": f'<function_calls><invoke name="Read"><parameter name="file_path">module_{i}.py</parameter></invoke></function_calls>',
                    },
                    {
                        "role": "assistant",
                        "content": f"I found several improvement opportunities in module {i}.",
                    },
                ]
            )

        return messages

    @staticmethod
    def create_mixed_pattern_session() -> List[Dict]:
        """Create session with multiple pattern types"""
        messages = []

        # Start with normal interaction
        messages.extend(
            [
                {"role": "user", "content": "I need to build a complex data processing pipeline"},
                {
                    "role": "assistant",
                    "content": "I'll help you build a robust data processing pipeline.",
                },
            ]
        )

        # Add repeated file operations
        for i in range(6):
            messages.append(
                {
                    "role": "assistant",
                    "content": f'<function_calls><invoke name="Read"><parameter name="file_path">data_{i}.csv</parameter></invoke></function_calls>',
                }
            )

        # Add error patterns
        messages.extend(
            [
                {"role": "user", "content": "Getting parsing errors with the CSV files"},
                {"role": "assistant", "content": "Let me check the CSV format."},
                {"role": "user", "content": "Another error: encoding issue, this is frustrating"},
                {"role": "assistant", "content": "I'll handle the encoding properly."},
            ]
        )

        # Add more repeated operations
        for i in range(8):
            messages.append(
                {
                    "role": "assistant",
                    "content": f'<function_calls><invoke name="Bash"><parameter name="command">validate_data_{i}.py</parameter></invoke></function_calls>',
                }
            )

        # Add frustration indicators
        messages.extend(
            [
                {"role": "user", "content": "This is taking too long and doesn't seem to work"},
                {"role": "assistant", "content": "Let me optimize the approach."},
                {
                    "role": "user",
                    "content": "Still getting issues, I'm confused about the best approach",
                },
            ]
        )

        return messages

    @staticmethod
    def create_custom_session(
        tool_counts: Dict[str, int] = None,
        error_count: int = 0,
        frustration_indicators: int = 0,
        total_length: int = 20,
    ) -> List[Dict]:
        """Create custom session with specified patterns"""
        messages = [
            {"role": "user", "content": "Custom session for testing"},
            {"role": "assistant", "content": "I'll help with your custom requirements."},
        ]

        tool_counts = tool_counts or {}

        # Add tool usage
        for tool, count in tool_counts.items():
            for i in range(count):
                if tool == "bash":
                    content = f'<function_calls><invoke name="Bash"><parameter name="command">command_{i}</parameter></invoke></function_calls>'
                elif tool == "read":
                    content = f'<function_calls><invoke name="Read"><parameter name="file_path">file_{i}.py</parameter></invoke></function_calls>'
                elif tool == "write":
                    content = f'<function_calls><invoke name="Write"><parameter name="file_path">output_{i}.py</parameter></invoke></function_calls>'
                else:
                    content = (
                        f'<function_calls><invoke name="{tool.title()}"></invoke></function_calls>'
                    )

                messages.append({"role": "assistant", "content": content})

        # Add error patterns
        error_phrases = [
            "Getting an error: FileNotFoundError",
            "Error: permission denied",
            "Failed with ImportError",
            "Exception occurred during execution",
            "Traceback shows ValueError",
        ]

        for i in range(error_count):
            phrase = error_phrases[i % len(error_phrases)]
            messages.append({"role": "user", "content": phrase})

        # Add frustration indicators
        frustration_phrases = [
            "This doesn't work",
            "Still failing",
            "I'm confused",
            "Why isn't this working?",
            "This seems broken",
            "Getting stuck",
        ]

        for i in range(frustration_indicators):
            phrase = frustration_phrases[i % len(frustration_phrases)]
            messages.append({"role": "user", "content": phrase})

        # Pad to desired length
        while len(messages) < total_length:
            messages.extend(
                [
                    {"role": "user", "content": f"Additional request {len(messages)}"},
                    {"role": "assistant", "content": f"Additional response {len(messages)}"},
                ]
            )

        return messages[:total_length]


class MockFileSystem:
    """Mock file system operations for testing"""

    def __init__(self):
        self.files = {}
        self.directories = set()

    def create_temp_structure(self) -> Path:
        """Create temporary directory structure for testing"""
        temp_dir = Path(tempfile.mkdtemp())

        # Create .claude directory structure
        claude_dir = temp_dir / ".claude"
        claude_dir.mkdir(parents=True)

        runtime_dir = claude_dir / "runtime"
        runtime_dir.mkdir(parents=True)

        logs_dir = runtime_dir / "logs"
        logs_dir.mkdir(parents=True)

        queue_dir = runtime_dir / "improvement_queue"
        queue_dir.mkdir(parents=True)

        # Create some test files
        config_file = runtime_dir / "automation_config.json"
        config_file.write_text(
            json.dumps(
                {
                    "automation_enabled": True,
                    "trigger_thresholds": {
                        "min_pattern_severity": "medium",
                        "min_pattern_count": 2,
                        "cooldown_hours": 1,
                    },
                },
                indent=2,
            )
        )

        return temp_dir

    def cleanup_temp_structure(self, temp_dir: Path):
        """Clean up temporary directory structure"""
        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)


class TestMockInfrastructure:
    """Test the mock infrastructure itself"""

    def test_mock_github_api(self):
        """Test MockGitHubAPI functionality"""
        api = MockGitHubAPI()

        # Test successful issue creation
        issue = api.create_issue(
            title="Test Issue", body="Test Description", labels=["bug", "priority:high"]
        )

        assert issue["title"] == "Test Issue"
        assert issue["body"] == "Test Description"
        assert "bug" in issue["labels"]
        assert issue["state"] == "open"
        assert issue["number"] == 1

        # Test API call tracking
        calls = api.get_api_calls()
        assert len(calls) == 1
        assert calls[0]["action"] == "create_issue"

        # Test failure simulation
        api.set_failure_mode(True, "rate_limit")
        with pytest.raises(Exception, match="rate limit"):
            api.create_issue("Should Fail", "This should fail")

    def test_mock_github_cli(self):
        """Test MockGitHubCLI functionality"""
        api = MockGitHubAPI()
        cli = MockGitHubCLI(api)

        # Test successful command
        result = cli.mock_gh_command(
            [
                "gh",
                "issue",
                "create",
                "--title",
                "CLI Test",
                "--body",
                "CLI Description",
                "--label",
                "test",
            ]
        )

        assert result.returncode == 0
        assert "github.com" in result.stdout

        # Test failure simulation
        cli.set_failure_mode(True, "auth")
        result = cli.mock_gh_command(["gh", "issue", "create"])
        assert result.returncode == 1
        assert "authentication failed" in result.stderr

    def test_mock_session_data(self):
        """Test MockSessionData generators"""
        # Test simple session
        simple = MockSessionData.create_simple_session()
        assert len(simple) >= 4
        assert any(msg["role"] == "user" for msg in simple)
        assert any(msg["role"] == "assistant" for msg in simple)

        # Test repeated tool session
        repeated = MockSessionData.create_repeated_tool_session()
        bash_count = sum(1 for msg in repeated if "Bash" in msg.get("content", ""))
        assert bash_count >= 8

        # Test error pattern session
        errors = MockSessionData.create_error_pattern_session()
        error_keywords = ["error", "Error", "failed", "broken"]
        error_messages = [
            msg
            for msg in errors
            if any(keyword in msg.get("content", "") for keyword in error_keywords)
        ]
        assert len(error_messages) >= 3

        # Test custom session
        custom = MockSessionData.create_custom_session(
            tool_counts={"bash": 5, "read": 3},
            error_count=2,
            frustration_indicators=1,
            total_length=25,
        )
        assert len(custom) == 25

    def test_mock_filesystem(self):
        """Test MockFileSystem functionality"""
        fs = MockFileSystem()

        # Test temp structure creation
        temp_dir = fs.create_temp_structure()
        assert temp_dir.exists()
        assert (temp_dir / ".claude").exists()
        assert (temp_dir / ".claude" / "runtime").exists()

        # Test config file creation
        config_file = temp_dir / ".claude" / "runtime" / "automation_config.json"
        assert config_file.exists()

        config = json.loads(config_file.read_text())
        assert config["automation_enabled"] is True

        # Cleanup
        fs.cleanup_temp_structure(temp_dir)
        assert not temp_dir.exists()


# Utility functions for test setup


def create_github_mock_environment():
    """Create complete GitHub mock environment for testing"""
    api = MockGitHubAPI()
    cli = MockGitHubCLI(api)

    # Patch subprocess.run to use mock CLI
    def mock_subprocess_run(cmd, **kwargs):
        if cmd[0] == "gh":
            return cli.mock_gh_command(cmd, **kwargs)
        else:
            # For non-gh commands, return success
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

    return api, cli, mock_subprocess_run


def create_test_session_with_patterns(pattern_types: List[str]) -> List[Dict]:
    """Create test session with specific pattern types"""
    if "repeated_tools" in pattern_types:
        return MockSessionData.create_repeated_tool_session()
    elif "errors" in pattern_types:
        return MockSessionData.create_error_pattern_session()
    elif "frustration" in pattern_types:
        return MockSessionData.create_frustration_session()
    elif "long_session" in pattern_types:
        return MockSessionData.create_long_session()
    elif "mixed" in pattern_types:
        return MockSessionData.create_mixed_pattern_session()
    else:
        return MockSessionData.create_simple_session()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
