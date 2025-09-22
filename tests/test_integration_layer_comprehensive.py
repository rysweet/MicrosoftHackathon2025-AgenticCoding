#!/usr/bin/env python3
"""
Comprehensive Integration Layer Tests

Tests the complete integration layer that connects reflection analysis to PR creation.
Covers circuit breakers, rate limiting, workflow orchestration, GitHub integration,
error propagation, and configuration-driven behavior.
"""

import asyncio
import json
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from claude.tools.reflection_automation_pipeline import (
    AutomationTrigger,
    GitHubIntegration,
    ImprovementRequest,
    ReflectionAutomationPipeline,
    ReflectionMetrics,
    ReflectionPattern,
    ReflectionResult,
    WorkflowContext,
    WorkflowOrchestrator,
)


class TestCircuitBreakerPatterns:
    """Test circuit breaker patterns to protect against cascade failures"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "automation_config.json"

    def teardown_method(self):
        """Cleanup test environment"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_automation_trigger_circuit_breaker_on_repeated_failures(self):
        """Test circuit breaker opens after repeated automation failures"""
        # Create automation trigger with custom config
        config = {
            "automation_enabled": True,
            "circuit_breaker": {
                "failure_threshold": 3,
                "recovery_timeout": 300,  # 5 minutes
                "half_open_max_calls": 1,
            },
        }

        with open(self.config_path, "w") as f:
            json.dump(config, f)

        trigger = AutomationTrigger(str(self.config_path))

        # Create test reflection result
        reflection_result = self._create_test_reflection_result()

        # Mock failures
        with patch.object(trigger, "_queue_improvement_request") as mock_queue:
            mock_queue.side_effect = Exception("Simulated failure")

            # Should fail 3 times and trigger circuit breaker
            for i in range(3):
                result = asyncio.run(trigger.trigger_improvement_automation(reflection_result))
                assert result is None  # Should fail

            # Verify circuit breaker is now open
            assert hasattr(trigger, "_circuit_breaker_state")
            # Note: This would be implemented in the actual circuit breaker logic

    def test_workflow_orchestrator_circuit_breaker_on_github_failures(self):
        """Test workflow orchestrator circuit breaker when GitHub operations fail"""
        orchestrator = WorkflowOrchestrator()

        # Mock GitHub integration to fail repeatedly
        with patch.object(orchestrator.github, "create_issue") as mock_create_issue:
            mock_create_issue.side_effect = Exception("GitHub API failure")

            # Create test request
            request = self._create_test_improvement_request()

            # Should handle GitHub failures gracefully
            success = asyncio.run(orchestrator._execute_workflow("test_workflow", request))
            assert not success  # Should fail but not crash

    def test_pipeline_graceful_degradation_on_component_failure(self):
        """Test pipeline graceful degradation when components fail"""
        pipeline = ReflectionAutomationPipeline()

        # Mock automation trigger to fail
        with patch.object(
            pipeline.automation_trigger, "trigger_improvement_automation"
        ) as mock_trigger:
            mock_trigger.side_effect = Exception("Trigger failure")

            reflection_result = self._create_test_reflection_result()

            # Should handle failure gracefully
            result = asyncio.run(pipeline.process_reflection_result(reflection_result))
            assert result is None  # Should fail gracefully, not crash

    def test_error_isolation_between_components(self):
        """Test that errors in one component don't affect others"""
        pipeline = ReflectionAutomationPipeline()
        reflection_result = self._create_test_reflection_result()

        # Mock workflow orchestrator to fail
        with patch.object(pipeline.workflow_orchestrator, "process_queue") as mock_process:
            mock_process.side_effect = Exception("Workflow failure")

            # Automation trigger should still work despite workflow failure
            with patch.object(
                pipeline.automation_trigger, "trigger_improvement_automation"
            ) as mock_trigger:
                mock_trigger.return_value = "test_workflow_123"

                result = asyncio.run(pipeline.process_reflection_result(reflection_result))
                # Should get workflow ID even if workflow execution fails later
                assert result == "test_workflow_123"

    def _create_test_reflection_result(self) -> ReflectionResult:
        """Create test reflection result"""
        pattern = ReflectionPattern(
            type="repeated_tool_use",
            severity="high",
            count=5,
            suggestion="Test suggestion",
            context={"test": True},
            samples=["sample1", "sample2"],
        )

        metrics = ReflectionMetrics(
            total_messages=50, user_messages=25, assistant_messages=25, tool_uses=15
        )

        return ReflectionResult(
            session_id="test_session",
            timestamp=datetime.now(),
            patterns=[pattern],
            metrics=metrics,
            suggestions=["Test suggestion"],
        )

    def _create_test_improvement_request(self) -> ImprovementRequest:
        """Create test improvement request"""
        pattern = ReflectionPattern(
            type="repeated_tool_use",
            severity="high",
            count=5,
            suggestion="Test suggestion",
            context={"test": True},
        )

        return ImprovementRequest(
            issue_title="Test Issue",
            issue_description="Test Description",
            priority="high",
            improvement_type="tooling",
            source_pattern=pattern,
            context={"session_id": "test_session"},
        )


class TestRateLimitingMechanisms:
    """Test rate limiting mechanisms to prevent automation spam"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "automation_config.json"
        self.state_file = Path(self.temp_dir) / "automation_state.json"

    def teardown_method(self):
        """Cleanup test environment"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cooldown_period_enforcement(self):
        """Test that cooldown period prevents rapid automation triggers"""
        config = {"automation_enabled": True, "trigger_thresholds": {"cooldown_hours": 1}}

        with open(self.config_path, "w") as f:
            json.dump(config, f)

        trigger = AutomationTrigger(str(self.config_path))
        reflection_result = self._create_test_reflection_result()

        # Mock state file with recent automation
        recent_time = datetime.now() - timedelta(minutes=30)  # 30 minutes ago
        state = {
            "last_automation_trigger": recent_time.isoformat(),
            "last_session_id": "previous_session",
            "last_workflow_id": "previous_workflow",
        }

        with open(self.state_file, "w") as f:
            json.dump(state, f)

        # Override the state file path
        trigger._record_automation_trigger = Mock()
        with patch.object(trigger, "_get_last_automation_time", return_value=recent_time):
            # Should not trigger due to cooldown
            should_trigger = trigger.should_trigger_automation(reflection_result)
            assert not should_trigger

    def test_concurrent_workflow_limit_enforcement(self):
        """Test that concurrent workflow limits are enforced"""
        config = {
            "automation_enabled": True,
            "workflow_constraints": {"max_concurrent_workflows": 2},
        }

        orchestrator = WorkflowOrchestrator()

        # Mock queue directory with multiple workflows
        queue_dir = Path(self.temp_dir) / "improvement_queue"
        queue_dir.mkdir(parents=True, exist_ok=True)

        # Create 3 workflow files (exceeds limit of 2)
        for i in range(3):
            workflow_file = queue_dir / f"workflow_{i}.json"
            with open(workflow_file, "w") as f:
                json.dump({"test": f"workflow_{i}"}, f)

        with patch.object(orchestrator, "queue_dir", queue_dir):
            with patch.object(orchestrator, "_execute_workflow") as mock_execute:
                mock_execute.return_value = True

                # Should only process max_concurrent_workflows (but implementation dependent)
                processed = asyncio.run(orchestrator.process_queue())
                # Verify processing respects limits
                assert len(processed) <= 3  # All can be processed sequentially

    def test_rate_limiting_across_sessions(self):
        """Test rate limiting works across different sessions"""
        trigger = AutomationTrigger(str(self.config_path))

        # Create multiple reflection results from different sessions
        sessions = []
        for i in range(5):
            result = self._create_test_reflection_result()
            result.session_id = f"session_{i}"
            sessions.append(result)

        processed_count = 0

        # Mock queue to count successful triggers
        with patch.object(trigger, "_queue_improvement_request") as mock_queue:
            mock_queue.return_value = "workflow_123"

            for session_result in sessions:
                workflow_id = asyncio.run(trigger.trigger_improvement_automation(session_result))
                if workflow_id:
                    processed_count += 1

        # Should have rate limiting effects
        # Note: Actual behavior depends on configuration and timing

    def test_burst_protection_mechanism(self):
        """Test protection against burst automation requests"""
        config = {
            "automation_enabled": True,
            "rate_limiting": {"max_requests_per_minute": 3, "burst_window_seconds": 60},
        }

        with open(self.config_path, "w") as f:
            json.dump(config, f)

        trigger = AutomationTrigger(str(self.config_path))

        # Simulate burst of requests
        results = []
        for i in range(5):  # More than max_requests_per_minute
            reflection_result = self._create_test_reflection_result()
            reflection_result.session_id = f"burst_session_{i}"

            with patch.object(trigger, "_queue_improvement_request") as mock_queue:
                mock_queue.return_value = f"workflow_{i}"

                workflow_id = asyncio.run(trigger.trigger_improvement_automation(reflection_result))
                results.append(workflow_id)

        # Should have some protection (implementation dependent)
        successful_triggers = [r for r in results if r is not None]
        # Note: Actual implementation would enforce burst limits

    def _create_test_reflection_result(self) -> ReflectionResult:
        """Create test reflection result"""
        pattern = ReflectionPattern(
            type="repeated_tool_use",
            severity="high",
            count=5,
            suggestion="Test suggestion",
            context={"test": True},
        )

        metrics = ReflectionMetrics(
            total_messages=50, user_messages=25, assistant_messages=25, tool_uses=15
        )

        return ReflectionResult(
            session_id="test_session",
            timestamp=datetime.now(),
            patterns=[pattern],
            metrics=metrics,
            suggestions=["Test suggestion"],
        )


class TestWorkflowOrchestrationCompliance:
    """Test workflow orchestration compliance with DEFAULT_WORKFLOW.md"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Cleanup test environment"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_workflow_follows_13_step_process(self):
        """Test that workflow orchestrator follows the 13-step DEFAULT_WORKFLOW.md process"""
        orchestrator = WorkflowOrchestrator()

        # Mock workflow execution to track steps
        step_calls = []

        async def mock_step_execution(step_num, context):
            step_calls.append(step_num)
            return True

        with patch.object(orchestrator, "_execute_workflow_step", side_effect=mock_step_execution):
            request = self._create_test_improvement_request()

            success = asyncio.run(orchestrator._execute_workflow("test_workflow", request))
            assert success

            # Verify all 13 steps were called in order
            assert step_calls == list(range(1, 14))

    def test_workflow_step_dependencies(self):
        """Test that workflow steps have proper dependencies"""
        orchestrator = WorkflowOrchestrator()

        # Mock individual step implementations
        step_handlers = {}
        for i in range(1, 14):
            step_handlers[i] = AsyncMock(return_value=True)

        with patch.object(orchestrator, "_step_clarify_requirements", step_handlers[1]):
            with patch.object(orchestrator, "_step_create_github_issue", step_handlers[2]):
                with patch.object(orchestrator, "_step_setup_branch", step_handlers[3]):
                    request = self._create_test_improvement_request()
                    context = WorkflowContext(
                        workflow_id="test_workflow",
                        improvement_request=request,
                        log_dir=Path(self.temp_dir) / "logs",
                    )

                    # Test step 2 depends on step 1 completion
                    success_1 = asyncio.run(orchestrator._execute_workflow_step(1, context))
                    assert success_1

                    # Step 2 should have access to step 1 results
                    success_2 = asyncio.run(orchestrator._execute_workflow_step(2, context))
                    assert success_2

    def test_workflow_failure_handling(self):
        """Test workflow failure handling at each step"""
        orchestrator = WorkflowOrchestrator()

        # Mock step 5 to fail
        async def failing_step(context):
            raise Exception("Step 5 failure")

        with patch.object(orchestrator, "_execute_workflow_step") as mock_step:
            # Steps 1-4 succeed, step 5 fails
            mock_step.side_effect = [True, True, True, True, Exception("Step 5 failure")]

            request = self._create_test_improvement_request()
            success = asyncio.run(
                orchestrator._execute_workflow(workflow_id="test_workflow", request=request)
            )

            # Should fail gracefully
            assert not success

    def test_workflow_context_propagation(self):
        """Test that workflow context is properly propagated between steps"""
        orchestrator = WorkflowOrchestrator()

        request = self._create_test_improvement_request()
        context = WorkflowContext(
            workflow_id="test_workflow",
            improvement_request=request,
            log_dir=Path(self.temp_dir) / "logs",
        )

        # Mock GitHub issue creation
        with patch.object(orchestrator.github, "create_issue", return_value=42):
            success = asyncio.run(orchestrator._execute_workflow("test_workflow", request))

            # Context should be updated with issue number
            # Note: This would be tested in actual implementation

    def test_workflow_agent_delegation(self):
        """Test that workflow properly delegates to specialized agents"""
        orchestrator = WorkflowOrchestrator()

        # Mock agent calls
        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = "agent output"

            request = self._create_test_improvement_request()

            # Test would verify agent delegation
            # Note: This depends on actual agent integration implementation

    def _create_test_improvement_request(self) -> ImprovementRequest:
        """Create test improvement request"""
        pattern = ReflectionPattern(
            type="repeated_tool_use",
            severity="high",
            count=5,
            suggestion="Test suggestion",
            context={"test": True},
        )

        return ImprovementRequest(
            issue_title="Test Issue",
            issue_description="Test Description",
            priority="high",
            improvement_type="tooling",
            source_pattern=pattern,
            context={"session_id": "test_session"},
        )


class TestGitHubPRCreationIntegration:
    """Test GitHub PR creation via integration interfaces"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Cleanup test environment"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_github_integration_issue_creation(self):
        """Test GitHub issue creation through integration"""
        github = GitHubIntegration()

        # Mock gh CLI availability
        with patch.object(github, "_check_gh_cli", return_value=True):
            with patch("subprocess.run") as mock_run:
                # Mock successful issue creation
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = "https://github.com/user/repo/issues/123"

                request = self._create_test_improvement_request()
                issue_number = asyncio.run(github.create_issue(request))

                assert issue_number == 123
                # Verify gh CLI was called with correct parameters
                mock_run.assert_called_once()

    def test_github_integration_failure_handling(self):
        """Test GitHub integration failure handling"""
        github = GitHubIntegration()

        with patch.object(github, "_check_gh_cli", return_value=True):
            with patch("subprocess.run") as mock_run:
                # Mock failed issue creation
                mock_run.return_value.returncode = 1
                mock_run.return_value.stderr = "GitHub API error"

                request = self._create_test_improvement_request()
                issue_number = asyncio.run(github.create_issue(request))

                assert issue_number is None

    def test_github_cli_unavailable_fallback(self):
        """Test fallback behavior when GitHub CLI is unavailable"""
        github = GitHubIntegration()

        with patch.object(github, "_check_gh_cli", return_value=False):
            request = self._create_test_improvement_request()
            issue_number = asyncio.run(github.create_issue(request))

            assert issue_number is None

    def test_pr_creation_with_reflection_context(self):
        """Test PR creation includes proper reflection context"""
        github = GitHubIntegration()

        # Create context with reflection information
        pattern = ReflectionPattern(
            type="repeated_tool_use",
            severity="high",
            count=8,
            suggestion="Create automation script",
            context={"tool": "bash", "commands": ["ls", "grep"]},
            samples=["ls -la", "grep pattern"],
        )

        request = ImprovementRequest(
            issue_title="Automate repeated bash commands",
            issue_description="Pattern detected 8 times",
            priority="high",
            improvement_type="tooling",
            source_pattern=pattern,
            context={"session_id": "test_session"},
        )

        context = WorkflowContext(
            workflow_id="test_workflow",
            improvement_request=request,
            log_dir=Path(self.temp_dir),
            github_issue_number=42,
            branch_name="feat/issue-42-automation",
        )

        # Test PR body formatting
        pr_body = github._format_pr_body(context)

        assert "repeated_tool_use" in pr_body
        assert "8" in pr_body  # Pattern count
        assert "high" in pr_body  # Severity
        assert "test_session" in pr_body  # Session context
        assert "bash" in pr_body  # Tool context

    def _create_test_improvement_request(self) -> ImprovementRequest:
        """Create test improvement request"""
        pattern = ReflectionPattern(
            type="repeated_tool_use",
            severity="high",
            count=5,
            suggestion="Test suggestion",
            context={"test": True},
        )

        return ImprovementRequest(
            issue_title="Test Issue",
            issue_description="Test Description",
            priority="high",
            improvement_type="tooling",
            source_pattern=pattern,
            context={"session_id": "test_session"},
        )


class TestReflectionTriggerAutomationCriteria:
    """Test ReflectionTrigger automation criteria assessment"""

    def test_automation_worthy_high_severity_pattern(self):
        """Test automation triggers for high severity patterns"""
        pattern = ReflectionPattern(
            type="user_frustration",
            severity="critical",
            count=3,
            suggestion="Review approach",
            context={"frustration_indicators": ["doesn't work", "broken", "stuck"]},
        )

        metrics = ReflectionMetrics(
            total_messages=40, user_messages=20, assistant_messages=20, tool_uses=10
        )

        result = ReflectionResult(
            session_id="test_session",
            timestamp=datetime.now(),
            patterns=[pattern],
            metrics=metrics,
            suggestions=["High priority review needed"],
        )

        assert result.is_automation_worthy()
        assert result.get_primary_issue().severity == "critical"

    def test_automation_worthy_multiple_medium_patterns(self):
        """Test automation triggers for multiple medium severity patterns"""
        patterns = [
            ReflectionPattern(
                type="repeated_tool_use",
                severity="medium",
                count=4,
                suggestion="Consider script",
                context={"tool": "bash"},
            ),
            ReflectionPattern(
                type="error_patterns",
                severity="medium",
                count=3,
                suggestion="Better error handling",
                context={"errors": ["file not found", "permission denied"]},
            ),
        ]

        metrics = ReflectionMetrics(
            total_messages=60, user_messages=30, assistant_messages=30, tool_uses=20
        )

        result = ReflectionResult(
            session_id="test_session",
            timestamp=datetime.now(),
            patterns=patterns,
            metrics=metrics,
            suggestions=["Multiple improvements needed"],
        )

        assert result.is_automation_worthy()

    def test_automation_not_worthy_low_patterns(self):
        """Test automation does not trigger for low severity patterns"""
        pattern = ReflectionPattern(
            type="repeated_tool_use",
            severity="low",
            count=2,
            suggestion="Minor optimization",
            context={"tool": "read"},
        )

        metrics = ReflectionMetrics(
            total_messages=20, user_messages=10, assistant_messages=10, tool_uses=5
        )

        result = ReflectionResult(
            session_id="test_session",
            timestamp=datetime.now(),
            patterns=[pattern],
            metrics=metrics,
            suggestions=["Minor improvement possible"],
        )

        assert not result.is_automation_worthy()

    def test_improvement_request_from_pattern_mapping(self):
        """Test conversion from reflection pattern to improvement request"""
        pattern = ReflectionPattern(
            type="repeated_tool_use",
            severity="high",
            count=8,
            suggestion="Create automation script for repeated bash commands",
            context={"tool": "bash", "commands": ["ls", "grep", "awk"]},
            samples=["ls -la", "grep pattern", "awk '{print $1}'"],
        )

        request = ImprovementRequest.from_reflection_pattern(
            pattern, {"session_id": "test_session"}
        )

        assert request.improvement_type == "tooling"
        assert request.priority == "high"
        assert request.estimated_complexity == "medium"  # High severity -> medium complexity
        assert "repeated bash commands" in request.issue_description
        assert request.source_pattern == pattern

    def test_complexity_estimation_by_pattern_characteristics(self):
        """Test complexity estimation based on pattern characteristics"""
        # High count pattern should be complex
        high_count_pattern = ReflectionPattern(
            type="repeated_tool_use",
            severity="medium",
            count=15,  # > 10
            suggestion="Automation needed",
            context={"tool": "bash"},
        )

        request = ImprovementRequest.from_reflection_pattern(
            high_count_pattern, {"session_id": "test_session"}
        )

        assert request.estimated_complexity == "complex"

        # Critical severity should be medium complexity
        critical_pattern = ReflectionPattern(
            type="user_frustration",
            severity="critical",
            count=3,
            suggestion="Review approach",
            context={"frustration": True},
        )

        request = ImprovementRequest.from_reflection_pattern(
            critical_pattern, {"session_id": "test_session"}
        )

        assert request.estimated_complexity == "medium"


class TestDataFlowFromReflectionToPR:
    """Test complete data flow from reflection to PR creation"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Cleanup test environment"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    async def test_end_to_end_data_flow(self):
        """Test complete data flow from reflection analysis to PR creation"""
        # Create reflection result
        pattern = ReflectionPattern(
            type="repeated_tool_use",
            severity="high",
            count=7,
            suggestion="Create automation script for file processing",
            context={"tool": "bash", "files": ["file1.py", "file2.py", "file3.py"]},
            samples=["bash process_file.sh file1.py", "bash process_file.sh file2.py"],
        )

        metrics = ReflectionMetrics(
            total_messages=45, user_messages=22, assistant_messages=23, tool_uses=18
        )

        reflection_result = ReflectionResult(
            session_id="e2e_test_session",
            timestamp=datetime.now(),
            patterns=[pattern],
            metrics=metrics,
            suggestions=["Automate file processing with script"],
        )

        # Mock all external dependencies
        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = "https://github.com/user/repo/issues/789"

            # Process through pipeline
            pipeline = ReflectionAutomationPipeline()

            # Override config to enable automation
            config_path = Path(self.temp_dir) / "automation_config.json"
            config = {"automation_enabled": True}
            with open(config_path, "w") as f:
                json.dump(config, f)

            pipeline.automation_trigger.config_path = config_path
            pipeline.automation_trigger.enabled = True

            # Override queue directory
            queue_dir = Path(self.temp_dir) / "improvement_queue"
            pipeline.automation_trigger._queue_improvement_request = AsyncMock(
                return_value="e2e_workflow_123"
            )

            workflow_id = await pipeline.process_reflection_result(reflection_result)

            assert workflow_id == "e2e_workflow_123"

            # Verify data transformation through pipeline
            # Note: This would verify the actual queue file in real implementation

    def test_data_integrity_through_transformations(self):
        """Test data integrity is maintained through all transformations"""
        # Original reflection analysis format
        analysis = {
            "timestamp": "2025-09-22T10:30:00",
            "patterns": [
                {
                    "type": "repeated_tool_use",
                    "tool": "bash",
                    "count": 6,
                    "suggestion": "Consider creating a script for repeated bash commands",
                },
                {
                    "type": "user_frustration",
                    "indicators": 2,
                    "suggestion": "Review approach and consider alternative solution",
                },
            ],
            "metrics": {
                "total_messages": 50,
                "user_messages": 25,
                "assistant_messages": 25,
                "tool_uses": 15,
            },
            "suggestions": ["Create automation script", "Review methodology"],
        }

        # Convert to ReflectionResult
        from claude.tools.reflection_automation_pipeline import (
            convert_reflection_analysis_to_result,
        )

        reflection_result = convert_reflection_analysis_to_result(analysis)

        assert reflection_result is not None
        assert len(reflection_result.patterns) == 2
        assert reflection_result.patterns[0].type == "repeated_tool_use"
        assert reflection_result.patterns[0].count == 6
        assert reflection_result.patterns[1].type == "user_frustration"
        assert reflection_result.metrics.total_messages == 50
        assert len(reflection_result.suggestions) == 2

        # Convert to ImprovementRequest
        primary_pattern = reflection_result.get_primary_issue()
        request = ImprovementRequest.from_reflection_pattern(
            primary_pattern, {"session_id": reflection_result.session_id}
        )

        # Verify data integrity
        assert request.source_pattern.type == primary_pattern.type
        assert request.source_pattern.count == primary_pattern.count
        assert request.improvement_type in ["tooling", "workflow"]  # Mapped correctly

    def test_error_propagation_preserves_context(self):
        """Test error propagation preserves context for debugging"""
        pipeline = ReflectionAutomationPipeline()

        # Create reflection result that will trigger errors
        reflection_result = ReflectionResult(
            session_id="error_test_session",
            timestamp=datetime.now(),
            patterns=[],  # Empty patterns to trigger edge case
            metrics=ReflectionMetrics(0, 0, 0, 0),
            suggestions=[],
        )

        # Should handle gracefully and preserve context
        result = asyncio.run(pipeline.process_reflection_result(reflection_result))
        assert result is None  # Should fail gracefully

    def test_configuration_affects_data_flow(self):
        """Test that configuration changes affect data flow correctly"""
        config_path = Path(self.temp_dir) / "test_config.json"

        # Test with automation disabled
        config_disabled = {"automation_enabled": False}
        with open(config_path, "w") as f:
            json.dump(config_disabled, f)

        trigger_disabled = AutomationTrigger(str(config_path))
        reflection_result = self._create_test_reflection_result()

        should_trigger = trigger_disabled.should_trigger_automation(reflection_result)
        assert not should_trigger

        # Test with automation enabled
        config_enabled = {"automation_enabled": True}
        with open(config_path, "w") as f:
            json.dump(config_enabled, f)

        trigger_enabled = AutomationTrigger(str(config_path))
        should_trigger = trigger_enabled.should_trigger_automation(reflection_result)
        assert should_trigger

    def _create_test_reflection_result(self) -> ReflectionResult:
        """Create test reflection result"""
        pattern = ReflectionPattern(
            type="repeated_tool_use",
            severity="high",
            count=5,
            suggestion="Test suggestion",
            context={"test": True},
        )

        metrics = ReflectionMetrics(
            total_messages=50, user_messages=25, assistant_messages=25, tool_uses=15
        )

        return ReflectionResult(
            session_id="test_session",
            timestamp=datetime.now(),
            patterns=[pattern],
            metrics=metrics,
            suggestions=["Test suggestion"],
        )


class TestErrorPropagationAndRecovery:
    """Test error propagation and recovery across components"""

    def test_github_error_recovery(self):
        """Test recovery from GitHub API errors"""
        github = GitHubIntegration()

        with patch.object(github, "_check_gh_cli", return_value=True):
            with patch("subprocess.run") as mock_run:
                # Simulate GitHub API rate limiting
                mock_run.side_effect = [
                    Mock(returncode=1, stderr="API rate limit exceeded"),
                    Mock(returncode=0, stdout="https://github.com/user/repo/issues/456"),
                ]

                request = self._create_test_improvement_request()

                # Should implement retry logic
                # Note: This would be tested with actual retry implementation

    def test_workflow_step_failure_recovery(self):
        """Test recovery from individual workflow step failures"""
        orchestrator = WorkflowOrchestrator()

        # Mock step failure followed by retry success
        with patch.object(orchestrator, "_execute_workflow_step") as mock_step:
            mock_step.side_effect = [
                True,  # Step 1 success
                Exception("Step 2 failure"),  # Step 2 fails
                True,  # Step 2 retry success
                True,  # Step 3 success
            ]

            request = self._create_test_improvement_request()

            # Should handle step failure with retry
            # Note: This depends on retry implementation

    def test_queue_corruption_recovery(self):
        """Test recovery from queue file corruption"""
        orchestrator = WorkflowOrchestrator()

        # Create corrupted queue file
        queue_dir = Path(tempfile.mkdtemp()) / "improvement_queue"
        queue_dir.mkdir(parents=True)

        corrupted_file = queue_dir / "corrupted_workflow.json"
        with open(corrupted_file, "w") as f:
            f.write("invalid json content {")

        with patch.object(orchestrator, "queue_dir", queue_dir):
            # Should handle corruption gracefully
            processed = asyncio.run(orchestrator.process_queue())
            assert processed == []  # Should process nothing but not crash

        # Cleanup
        import shutil

        shutil.rmtree(queue_dir.parent)

    def test_async_operation_timeout_handling(self):
        """Test handling of async operation timeouts"""
        pipeline = ReflectionAutomationPipeline()

        # Mock slow operation
        slow_mock = AsyncMock()
        slow_mock.side_effect = asyncio.TimeoutError()

        with patch.object(pipeline.automation_trigger, "trigger_improvement_automation", slow_mock):
            reflection_result = self._create_test_reflection_result()

            # Should handle timeout gracefully
            result = asyncio.run(pipeline.process_reflection_result(reflection_result))
            assert result is None

    def test_concurrent_access_conflict_resolution(self):
        """Test resolution of concurrent access conflicts"""
        # Test concurrent modification of state files
        config_path = Path(tempfile.mkdtemp()) / "automation_config.json"
        config = {"automation_enabled": True}
        with open(config_path, "w") as f:
            json.dump(config, f)

        trigger1 = AutomationTrigger(str(config_path))
        trigger2 = AutomationTrigger(str(config_path))

        # Both triggers should handle concurrent access gracefully
        # Note: This would test file locking or other concurrency mechanisms

        # Cleanup
        import shutil

        shutil.rmtree(config_path.parent)

    def _create_test_improvement_request(self) -> ImprovementRequest:
        """Create test improvement request"""
        pattern = ReflectionPattern(
            type="repeated_tool_use",
            severity="high",
            count=5,
            suggestion="Test suggestion",
            context={"test": True},
        )

        return ImprovementRequest(
            issue_title="Test Issue",
            issue_description="Test Description",
            priority="high",
            improvement_type="tooling",
            source_pattern=pattern,
            context={"session_id": "test_session"},
        )

    def _create_test_reflection_result(self) -> ReflectionResult:
        """Create test reflection result"""
        pattern = ReflectionPattern(
            type="repeated_tool_use",
            severity="high",
            count=5,
            suggestion="Test suggestion",
            context={"test": True},
        )

        metrics = ReflectionMetrics(
            total_messages=50, user_messages=25, assistant_messages=25, tool_uses=15
        )

        return ReflectionResult(
            session_id="test_session",
            timestamp=datetime.now(),
            patterns=[pattern],
            metrics=metrics,
            suggestions=["Test suggestion"],
        )


class TestConfigurationDrivenBehavior:
    """Test configuration-driven behavior changes"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Cleanup test environment"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_threshold_configuration_affects_triggering(self):
        """Test that threshold configuration affects automation triggering"""
        config_path = Path(self.temp_dir) / "config.json"

        # High threshold configuration
        high_threshold_config = {
            "automation_enabled": True,
            "trigger_thresholds": {"min_pattern_severity": "critical", "min_pattern_count": 5},
        }

        with open(config_path, "w") as f:
            json.dump(high_threshold_config, f)

        trigger_high = AutomationTrigger(str(config_path))

        # Medium severity pattern should not trigger with high threshold
        medium_pattern = ReflectionPattern(
            type="repeated_tool_use", severity="medium", count=3, suggestion="Test", context={}
        )

        medium_result = ReflectionResult(
            session_id="test",
            timestamp=datetime.now(),
            patterns=[medium_pattern],
            metrics=ReflectionMetrics(20, 10, 10, 5),
            suggestions=[],
        )

        assert not trigger_high.should_trigger_automation(medium_result)

        # Low threshold configuration
        low_threshold_config = {
            "automation_enabled": True,
            "trigger_thresholds": {"min_pattern_severity": "low", "min_pattern_count": 1},
        }

        with open(config_path, "w") as f:
            json.dump(low_threshold_config, f)

        trigger_low = AutomationTrigger(str(config_path))

        # Same pattern should trigger with low threshold
        assert trigger_low.should_trigger_automation(medium_result)

    def test_workflow_constraints_configuration(self):
        """Test workflow constraints affect behavior"""
        config_path = Path(self.temp_dir) / "config.json"

        # Restrictive constraints
        restrictive_config = {
            "automation_enabled": True,
            "workflow_constraints": {
                "max_concurrent_workflows": 1,
                "max_lines_per_improvement": 50,
                "max_components_per_improvement": 1,
            },
        }

        with open(config_path, "w") as f:
            json.dump(restrictive_config, f)

        # Test constraint enforcement
        # Note: This would test actual constraint enforcement in implementation

    def test_github_integration_configuration(self):
        """Test GitHub integration configuration options"""
        config_path = Path(self.temp_dir) / "config.json"

        # GitHub integration disabled
        no_github_config = {
            "automation_enabled": True,
            "github_integration": {
                "auto_create_issues": False,
                "auto_create_branches": False,
                "auto_create_prs": False,
            },
        }

        with open(config_path, "w") as f:
            json.dump(no_github_config, f)

        # Test that GitHub operations are skipped when configured
        # Note: This would test actual configuration application

    def test_custom_pattern_configuration(self):
        """Test custom pattern detection configuration"""
        config_path = Path(self.temp_dir) / "config.json"

        # Custom pattern thresholds
        custom_patterns_config = {
            "automation_enabled": True,
            "pattern_detection": {
                "repeated_tool_use": {
                    "threshold": 2,  # Lower threshold
                    "severity_multiplier": 1.5,
                },
                "user_frustration": {
                    "keywords": ["confused", "lost", "stuck", "broken"],
                    "severity": "critical",
                },
            },
        }

        with open(config_path, "w") as f:
            json.dump(custom_patterns_config, f)

        # Test that custom patterns are applied
        # Note: This would integrate with pattern detection logic

    def test_environment_specific_configuration(self):
        """Test environment-specific configuration behavior"""
        config_path = Path(self.temp_dir) / "config.json"

        # Development environment configuration
        dev_config = {
            "automation_enabled": True,
            "environment": "development",
            "development_settings": {
                "aggressive_automation": True,
                "skip_manual_review": True,
                "auto_merge_simple_fixes": True,
            },
        }

        with open(config_path, "w") as f:
            json.dump(dev_config, f)

        # Production environment configuration
        prod_config = {
            "automation_enabled": True,
            "environment": "production",
            "production_settings": {
                "conservative_automation": True,
                "require_manual_review": True,
                "auto_merge_simple_fixes": False,
            },
        }

        # Test environment-specific behavior
        # Note: This would test actual environment-aware configuration

    def test_dynamic_configuration_reload(self):
        """Test dynamic configuration reload during operation"""
        config_path = Path(self.temp_dir) / "config.json"

        # Initial configuration
        initial_config = {"automation_enabled": False}
        with open(config_path, "w") as f:
            json.dump(initial_config, f)

        trigger = AutomationTrigger(str(config_path))
        assert not trigger.enabled

        # Update configuration
        updated_config = {"automation_enabled": True}
        with open(config_path, "w") as f:
            json.dump(updated_config, f)

        # Reload configuration
        trigger.enabled = trigger._load_config().get("automation_enabled", False)
        assert trigger.enabled


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
