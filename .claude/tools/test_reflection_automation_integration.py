#!/usr/bin/env python3
"""
Integration tests for the reflection automation pipeline.
Demonstrates how the complete system works from reflection to PR creation.
"""

import asyncio
import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Import the integration components
from .reflection_automation_pipeline import (
    AutomationTrigger,
    GitHubIntegration,
    ImprovementRequest,
    ReflectionAutomationPipeline,
    ReflectionMetrics,
    ReflectionPattern,
    ReflectionResult,
    WorkflowOrchestrator,
    convert_reflection_analysis_to_result,
)


class TestReflectionResultCreation:
    """Test creating ReflectionResult from various inputs"""

    def test_create_reflection_result_with_patterns(self):
        """Test creating a reflection result with detected patterns"""
        pattern = ReflectionPattern(
            type="repeated_tool_use",
            severity="high",
            count=7,
            suggestion="Consider creating a script for repeated bash commands",
            context={"tool": "bash", "commands": ["ls", "grep", "find"]},
            samples=["ls -la", "grep pattern file.txt", "find . -name '*.py'"],
        )

        metrics = ReflectionMetrics(
            total_messages=45, user_messages=22, assistant_messages=23, tool_uses=12
        )

        result = ReflectionResult(
            session_id="test_session_001",
            timestamp=datetime.now(),
            patterns=[pattern],
            metrics=metrics,
            suggestions=["Create bash script automation"],
        )

        # Test automation worthiness
        assert result.is_automation_worthy() == True  # High severity pattern
        assert result.get_primary_issue() == pattern

    def test_convert_from_existing_reflection_format(self):
        """Test converting existing reflection analysis to ReflectionResult"""
        # Simulate existing reflection analysis format
        analysis = {
            "timestamp": "2025-01-20T10:30:00",
            "patterns": [
                {
                    "type": "repeated_tool_use",
                    "tool": "read",
                    "count": 6,
                    "suggestion": "Consider caching file contents or using targeted search",
                },
                {
                    "type": "error_patterns",
                    "count": 4,
                    "samples": ["File not found", "Permission denied", "Timeout error"],
                    "suggestion": "Add better error handling",
                },
            ],
            "metrics": {
                "total_messages": 38,
                "user_messages": 19,
                "assistant_messages": 19,
                "tool_uses": 8,
            },
            "suggestions": ["Cache frequently read files", "Improve error handling patterns"],
        }

        result = convert_reflection_analysis_to_result(analysis)

        assert result is not None
        assert len(result.patterns) == 2
        assert result.patterns[0].type == "repeated_tool_use"
        assert result.patterns[0].severity == "medium"  # 6 count = medium
        assert result.patterns[1].type == "error_patterns"
        assert result.patterns[1].severity == "low"  # 4 count = low
        assert result.is_automation_worthy() == False  # No high/critical patterns


class TestImprovementRequestTransformation:
    """Test transforming ReflectionPattern to ImprovementRequest"""

    def test_transform_repeated_tool_pattern(self):
        """Test transforming repeated tool use pattern"""
        pattern = ReflectionPattern(
            type="repeated_tool_use",
            severity="high",
            count=9,
            suggestion="Create automation script for repeated git commands",
            context={"tool": "bash", "git_commands": ["git status", "git add", "git commit"]},
        )

        request = ImprovementRequest.from_reflection_pattern(
            pattern, {"session_id": "test_session"}
        )

        assert request.improvement_type == "tooling"
        assert request.priority == "high"
        assert request.estimated_complexity == "medium"  # High severity = medium complexity
        assert "repeated tool use" in request.issue_title
        assert "9 times" in request.issue_description
        assert request.max_components == 3
        assert request.max_lines_of_code == 200

    def test_transform_error_pattern(self):
        """Test transforming error pattern"""
        pattern = ReflectionPattern(
            type="error_patterns",
            severity="medium",
            count=5,
            suggestion="Add better error handling for file operations",
            context={"error_types": ["FileNotFoundError", "PermissionError"]},
        )

        request = ImprovementRequest.from_reflection_pattern(
            pattern, {"session_id": "test_session"}
        )

        assert request.improvement_type == "error_handling"
        assert request.requires_security_review == True  # Error patterns need security review
        assert request.priority == "medium"


class TestAutomationTrigger:
    """Test automation trigger logic"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "automation_config.json"
            yield config_path

    def test_automation_trigger_enabled(self, temp_config_dir):
        """Test automation trigger when enabled"""
        # Create enabled config
        config = {"automation_enabled": True}
        temp_config_dir.write_text(json.dumps(config))

        trigger = AutomationTrigger(str(temp_config_dir))
        assert trigger.enabled == True

        # Create automation-worthy result
        pattern = ReflectionPattern(
            type="user_frustration",
            severity="critical",
            count=3,
            suggestion="Review approach - user showing frustration",
            context={},
        )

        result = ReflectionResult(
            session_id="test",
            timestamp=datetime.now(),
            patterns=[pattern],
            metrics=ReflectionMetrics(20, 10, 10, 5),
            suggestions=[],
        )

        assert trigger.should_trigger_automation(result) == True

    def test_automation_trigger_disabled(self, temp_config_dir):
        """Test automation trigger when disabled"""
        # Create disabled config
        config = {"automation_enabled": False}
        temp_config_dir.write_text(json.dumps(config))

        trigger = AutomationTrigger(str(temp_config_dir))
        assert trigger.enabled == False

        # Even critical patterns shouldn't trigger when disabled
        pattern = ReflectionPattern(
            type="user_frustration",
            severity="critical",
            count=5,
            suggestion="Critical issue",
            context={},
        )

        result = ReflectionResult(
            session_id="test",
            timestamp=datetime.now(),
            patterns=[pattern],
            metrics=ReflectionMetrics(20, 10, 10, 5),
            suggestions=[],
        )

        assert trigger.should_trigger_automation(result) == False


class TestGitHubIntegration:
    """Test GitHub integration functionality"""

    @patch("subprocess.run")
    def test_gh_cli_available(self, mock_run):
        """Test GitHub CLI availability check"""
        # Mock successful gh CLI check
        mock_run.return_value.returncode = 0

        github = GitHubIntegration()
        assert github.gh_available == True

    @patch("subprocess.run")
    def test_gh_cli_not_available(self, mock_run):
        """Test GitHub CLI not available"""
        # Mock failed gh CLI check
        mock_run.side_effect = FileNotFoundError()

        github = GitHubIntegration()
        assert github.gh_available == False

    @patch("subprocess.run")
    async def test_create_issue_success(self, mock_run):
        """Test successful issue creation"""
        # Mock gh CLI responses
        mock_run.side_effect = [
            Mock(returncode=0),  # gh --version check
            Mock(returncode=0, stdout="https://github.com/user/repo/issues/42"),  # issue create
        ]

        github = GitHubIntegration()

        request = ImprovementRequest(
            issue_title="Test improvement",
            issue_description="Test description",
            priority="medium",
            improvement_type="tooling",
            source_pattern=ReflectionPattern(
                type="test", severity="medium", count=1, suggestion="test", context={}
            ),
            context={},
        )

        issue_number = await github.create_issue(request)
        assert issue_number == 42

    def test_format_issue_body(self):
        """Test issue body formatting"""
        pattern = ReflectionPattern(
            type="repeated_tool_use",
            severity="high",
            count=8,
            suggestion="Create automation script",
            context={"tool": "bash"},
        )

        request = ImprovementRequest(
            issue_title="Automate repeated commands",
            issue_description="Detected repeated bash usage",
            priority="high",
            improvement_type="tooling",
            source_pattern=pattern,
            context={"session_id": "test_session"},
        )

        github = GitHubIntegration()
        body = github._format_issue_body(request)

        assert "Automated Improvement Request" in body
        assert "repeated_tool_use" in body
        assert "8" in body  # occurrence count
        assert "high" in body  # severity
        assert "tooling" in body  # improvement type


class TestWorkflowOrchestrator:
    """Test workflow orchestration"""

    @pytest.fixture
    def temp_queue_dir(self):
        """Create temporary queue directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            queue_dir = Path(temp_dir) / "improvement_queue"
            queue_dir.mkdir(parents=True)
            yield queue_dir

    def test_load_improvement_request(self, temp_queue_dir):
        """Test loading improvement request from queue file"""
        # Create sample queue file
        pattern = ReflectionPattern(
            type="test_pattern",
            severity="medium",
            count=3,
            suggestion="Test suggestion",
            context={"test": "context"},
        )

        request = ImprovementRequest(
            issue_title="Test",
            issue_description="Test desc",
            priority="medium",
            improvement_type="pattern",
            source_pattern=pattern,
            context={},
        )

        # Simulate queue file creation
        queue_file = temp_queue_dir / "test_workflow.json"

        # Convert to dict format as pipeline would save it
        import json
        from dataclasses import asdict

        request_dict = asdict(request)
        request_dict["source_pattern"] = asdict(pattern)

        with open(queue_file, "w") as f:
            json.dump(request_dict, f, default=str)

        # Test loading
        orchestrator = WorkflowOrchestrator()
        orchestrator.queue_dir = temp_queue_dir

        loaded_request = orchestrator._load_improvement_request(queue_file)

        assert loaded_request.issue_title == "Test"
        assert loaded_request.source_pattern.type == "test_pattern"
        assert loaded_request.source_pattern.count == 3


class TestCompleteIntegrationFlow:
    """Test the complete flow from reflection to automation"""

    @pytest.fixture
    def temp_runtime_dir(self):
        """Create temporary runtime directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_dir = Path(temp_dir)
            yield runtime_dir

    @patch.object(GitHubIntegration, "create_issue")
    async def test_complete_automation_flow(self, mock_create_issue, temp_runtime_dir):
        """Test complete flow from reflection result to automation"""
        # Mock GitHub integration
        mock_create_issue.return_value = 123

        # Create automation config
        config_file = temp_runtime_dir / "automation_config.json"
        config = {"automation_enabled": True}
        config_file.write_text(json.dumps(config))

        # Create pipeline with temp directories
        trigger = AutomationTrigger(str(config_file))
        trigger.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Set up queue directory
        queue_dir = temp_runtime_dir / "improvement_queue"
        queue_dir.mkdir(parents=True)

        # Create test reflection result
        pattern = ReflectionPattern(
            type="repeated_tool_use",
            severity="high",
            count=10,
            suggestion="Create automation for repeated git operations",
            context={"tool": "bash", "commands": ["git status", "git add", "git commit"]},
        )

        result = ReflectionResult(
            session_id="integration_test",
            timestamp=datetime.now(),
            patterns=[pattern],
            metrics=ReflectionMetrics(60, 30, 30, 15),
            suggestions=["Automate git workflow"],
        )

        # Override queue directory for trigger
        original_queue_method = trigger._queue_improvement_request

        async def mock_queue_method(request):
            workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            queue_file = queue_dir / f"{workflow_id}.json"

            from dataclasses import asdict

            request_dict = asdict(request)
            request_dict["source_pattern"] = asdict(request.source_pattern)

            with open(queue_file, "w") as f:
                json.dump(request_dict, f, default=str)

            return workflow_id

        trigger._queue_improvement_request = mock_queue_method

        # Process through pipeline
        pipeline = ReflectionAutomationPipeline()
        pipeline.automation_trigger = trigger

        workflow_id = await pipeline.process_reflection_result(result)

        # Verify workflow was created
        assert workflow_id is not None
        assert workflow_id.startswith("workflow_")

        # Verify queue file was created
        queue_files = list(queue_dir.glob("*.json"))
        assert len(queue_files) == 1

        # Verify queue file content
        with open(queue_files[0]) as f:
            queued_data = json.load(f)

        assert queued_data["improvement_type"] == "tooling"
        assert queued_data["priority"] == "high"
        assert "repeated tool use" in queued_data["issue_title"]


class TestStopHookIntegration:
    """Test integration with stop hook"""

    def test_convert_reflection_analysis_format(self):
        """Test converting existing reflection analysis to new format"""
        # Simulate analysis from reflection.py
        analysis = {
            "timestamp": "2025-01-20T15:30:00",
            "patterns": [
                {
                    "type": "repeated_tool_use",
                    "tool": "bash",
                    "count": 7,
                    "suggestion": "Used bash 7 times. Consider creating a tool or script for this repeated action",
                },
                {
                    "type": "user_frustration",
                    "indicators": 3,
                    "suggestion": "Review approach and consider alternative solution",
                },
            ],
            "metrics": {
                "total_messages": 55,
                "user_messages": 28,
                "assistant_messages": 27,
                "tool_uses": 12,
            },
            "suggestions": [
                "HIGH PRIORITY: User frustration detected. Consider reviewing the approach with the architect agent.",
                "Consider creating a script to automate these bash commands.",
            ],
        }

        result = convert_reflection_analysis_to_result(analysis)

        assert result is not None
        assert len(result.patterns) == 2

        # Check pattern conversion
        bash_pattern = next(p for p in result.patterns if p.type == "repeated_tool_use")
        assert bash_pattern.count == 7
        assert bash_pattern.severity == "medium"  # 7 occurrences

        frustration_pattern = next(p for p in result.patterns if p.type == "user_frustration")
        assert frustration_pattern.severity == "critical"  # Always critical

        # Should trigger automation due to critical frustration pattern
        assert result.is_automation_worthy() == True


def create_demo_messages() -> List[Dict]:
    """Create demo message history for testing"""
    return [
        {"role": "user", "content": "Help me optimize this script"},
        {
            "role": "assistant",
            "content": 'I\'ll help you optimize the script. <function_calls><invoke name="Read"><parameter name="file_path">/path/to/script.py</parameter></invoke></function_calls>',
        },
        {"role": "user", "content": "It's still not working properly"},
        {
            "role": "assistant",
            "content": 'Let me check again. <function_calls><invoke name="Read"><parameter name="file_path">/path/to/script.py</parameter></invoke></function_calls>',
        },
        {"role": "user", "content": "This is frustrating, why isn't it working?"},
        {
            "role": "assistant",
            "content": 'I understand your frustration. Let me try a different approach. <function_calls><invoke name="Bash"><parameter name="command">ls -la</parameter></invoke></function_calls>',
        },
        {"role": "user", "content": "Can you check the logs too?"},
        {
            "role": "assistant",
            "content": '<function_calls><invoke name="Bash"><parameter name="command">tail -f /var/log/app.log</parameter></invoke></function_calls>',
        },
        {
            "role": "assistant",
            "content": '<function_calls><invoke name="Bash"><parameter name="command">grep ERROR /var/log/app.log</parameter></invoke></function_calls>',
        },
        {
            "role": "assistant",
            "content": '<function_calls><invoke name="Read"><parameter name="file_path">/path/to/config.json</parameter></invoke></function_calls>',
        },
    ]


async def demo_complete_integration():
    """Demonstrate the complete integration flow"""
    print("🏴‍☠️ Ahoy! Running complete integration demonstration")

    # Create demo reflection result
    pattern1 = ReflectionPattern(
        type="repeated_tool_use",
        severity="high",
        count=8,
        suggestion="Consider creating a script for repeated bash commands",
        context={"tool": "bash", "commands": ["ls", "grep", "tail"]},
        samples=["ls -la", "grep ERROR log.txt", "tail -f app.log"],
    )

    pattern2 = ReflectionPattern(
        type="user_frustration",
        severity="critical",
        count=2,
        suggestion="Review approach - user showing frustration",
        context={"frustration_indicators": ["not working", "frustrating"]},
    )

    metrics = ReflectionMetrics(
        total_messages=45, user_messages=22, assistant_messages=23, tool_uses=12
    )

    reflection_result = ReflectionResult(
        session_id="demo_integration",
        timestamp=datetime.now(),
        patterns=[pattern1, pattern2],
        metrics=metrics,
        suggestions=[
            "HIGH PRIORITY: User frustration detected",
            "Create bash command automation script",
        ],
    )

    print(f"📊 Created reflection result with {len(reflection_result.patterns)} patterns")
    print(f"🎯 Automation worthy: {reflection_result.is_automation_worthy()}")

    # Process through pipeline
    pipeline = ReflectionAutomationPipeline()

    # Enable automation for demo
    config_path = Path(".claude/runtime/automation_config.json")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config = {"automation_enabled": True}
    config_path.write_text(json.dumps(config, indent=2))

    workflow_id = await pipeline.process_reflection_result(reflection_result)

    if workflow_id:
        print(f"✅ Automation triggered! Workflow ID: {workflow_id}")
        print("📁 Queue file created in .claude/runtime/improvement_queue/")

        # Show queue file content
        queue_file = Path(f".claude/runtime/improvement_queue/{workflow_id}.json")
        if queue_file.exists():
            with open(queue_file) as f:
                queue_data = json.load(f)
            print(f"📋 Issue title: {queue_data['issue_title']}")
            print(f"🔧 Improvement type: {queue_data['improvement_type']}")
            print(f"⚡ Priority: {queue_data['priority']}")

        # Process the queue (this would create GitHub issues, etc.)
        processed = await pipeline.workflow_orchestrator.process_queue()
        if processed:
            print(f"🚀 Processed workflows: {processed}")
        else:
            print("⏳ Queue processing completed (check logs for details)")

    else:
        print("❌ Automation not triggered")


if __name__ == "__main__":
    # Run specific tests
    print("Running integration tests...")

    # Test individual components
    test_reflection = TestReflectionResultCreation()
    test_reflection.test_create_reflection_result_with_patterns()
    print("✅ Reflection result creation tests passed")

    test_transform = TestImprovementRequestTransformation()
    test_transform.test_transform_repeated_tool_pattern()
    print("✅ Improvement request transformation tests passed")

    # Run complete integration demo
    print("\n" + "=" * 50)
    print("Running complete integration demonstration...")
    asyncio.run(demo_complete_integration())
    print("=" * 50)
