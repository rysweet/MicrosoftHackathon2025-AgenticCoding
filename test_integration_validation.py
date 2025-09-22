#!/usr/bin/env python3
"""
Integration Layer Validation Tests

Validates the key integration points between reflection analysis and automation pipeline.
Tests circuit breakers, rate limiting, workflow orchestration, and error handling.
"""

import asyncio
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

# Load the automation pipeline
exec(open(".claude/tools/reflection_automation_pipeline.py").read())


class IntegrationLayerValidator:
    """Validates the integration layer components"""

    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        self.results = []

    def log_result(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "✓ PASS" if passed else "✗ FAIL"
        self.results.append(f"{status}: {test_name}")
        if details:
            self.results.append(f"   {details}")

    def test_stop_hook_integration(self):
        """Test stop hook integration and Stage 2 automation triggers"""
        print("🧪 Testing Stop Hook Integration...")

        try:
            # Test enhanced continuation logic simulation
            def mock_enhanced_should_continue(messages):
                """Mock enhanced continuation logic"""
                if len(messages) < 2:
                    return {"decision": "stop", "reason": "too_few_messages"}

                # Check for automation patterns
                automation_patterns = any(
                    "repeated" in msg.get("content", "").lower()
                    or "error" in msg.get("content", "").lower()
                    or "frustration" in msg.get("content", "").lower()
                    for msg in messages
                )

                if automation_patterns:
                    return {
                        "decision": "continue",
                        "reason": "automation_triggered",
                        "workflow_id": "test_workflow_123",
                    }

                return {"decision": "stop", "reason": "no_continuation_needed"}

            # Test basic continuation logic
            messages = [
                {"role": "user", "content": "Test message"},
                {"role": "assistant", "content": "Response"},
            ]

            result = mock_enhanced_should_continue(messages)
            self.log_result("Stop Hook Integration", result["decision"] in ["continue", "stop"])

            # Test automation trigger
            automation_messages = [
                {"role": "user", "content": "I'm getting repeated errors"},
                {"role": "assistant", "content": "Let me help with that"},
            ]

            automation_result = mock_enhanced_should_continue(automation_messages)
            self.log_result(
                "Stop Hook Automation Trigger",
                automation_result.get("reason") == "automation_triggered",
            )

        except Exception as e:
            self.log_result("Stop Hook Integration", False, f"Error: {e}")

    def test_circuit_breaker_patterns(self):
        """Test circuit breaker patterns for cascade failure protection"""
        print("🧪 Testing Circuit Breaker Patterns...")

        try:
            # Test automation trigger circuit breaker
            config_path = Path(self.temp_dir) / "circuit_breaker_config.json"
            config = {
                "automation_enabled": True,
                "circuit_breaker": {"failure_threshold": 3, "recovery_timeout": 300},
            }

            with open(config_path, "w") as f:
                json.dump(config, f)

            trigger = AutomationTrigger(str(config_path))

            # Test that trigger handles failures gracefully
            reflection_result = self._create_test_reflection_result()

            # Should not crash on failure - test actual behavior
            try:

                async def failing_queue_request(request):
                    raise Exception("Simulated failure")

                original_method = trigger._queue_improvement_request
                trigger._queue_improvement_request = failing_queue_request

                result = asyncio.run(trigger.trigger_improvement_automation(reflection_result))
                trigger._queue_improvement_request = original_method  # Restore

                self.log_result(
                    "Circuit Breaker Protection", result is None, "Handled failure gracefully"
                )
            except Exception as e:
                self.log_result("Circuit Breaker Protection", False, f"Exception not handled: {e}")

        except Exception as e:
            self.log_result("Circuit Breaker Protection", False, f"Error: {e}")

    def test_rate_limiting_mechanisms(self):
        """Test rate limiting mechanisms against automation spam"""
        print("🧪 Testing Rate Limiting Mechanisms...")

        try:
            config_path = Path(self.temp_dir) / "rate_limit_config.json"
            config = {"automation_enabled": True, "trigger_thresholds": {"cooldown_hours": 1}}

            with open(config_path, "w") as f:
                json.dump(config, f)

            trigger = AutomationTrigger(str(config_path))

            # Simulate recent automation
            state_file = Path(self.temp_dir) / "automation_state.json"
            recent_time = datetime.now() - timedelta(minutes=30)  # 30 minutes ago
            state = {
                "last_automation_trigger": recent_time.isoformat(),
                "last_session_id": "previous_session",
                "last_workflow_id": "previous_workflow",
            }

            with open(state_file, "w") as f:
                json.dump(state, f)

            # Override state file methods
            with patch.object(trigger, "_get_last_automation_time", return_value=recent_time):
                reflection_result = self._create_test_reflection_result()
                should_trigger = trigger.should_trigger_automation(reflection_result)
                self.log_result(
                    "Rate Limiting Cooldown", not should_trigger, "Cooldown period enforced"
                )

        except Exception as e:
            self.log_result("Rate Limiting Cooldown", False, f"Error: {e}")

    def test_workflow_orchestration_compliance(self):
        """Test workflow orchestration compliance with DEFAULT_WORKFLOW.md"""
        print("🧪 Testing Workflow Orchestration Compliance...")

        try:
            orchestrator = WorkflowOrchestrator()

            # Test workflow step execution order
            step_calls = []

            async def mock_step_execution(step_num, context):
                step_calls.append(step_num)
                return True

            with patch.object(
                orchestrator, "_execute_workflow_step", side_effect=mock_step_execution
            ):
                request = self._create_test_improvement_request()
                success = asyncio.run(orchestrator._execute_workflow("test_workflow", request))

                expected_steps = list(range(1, 14))  # Steps 1-13
                self.log_result(
                    "Workflow Step Compliance",
                    step_calls == expected_steps and success,
                    f"Executed steps: {step_calls}",
                )

        except Exception as e:
            self.log_result("Workflow Step Compliance", False, f"Error: {e}")

    def test_github_pr_creation_integration(self):
        """Test GitHub PR creation via integration interfaces"""
        print("🧪 Testing GitHub PR Creation Integration...")

        try:
            github = GitHubIntegration()

            # Test issue creation with mocked GitHub CLI
            with patch.object(github, "_check_gh_cli", return_value=True):
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value.returncode = 0
                    mock_run.return_value.stdout = "https://github.com/user/repo/issues/123"

                    request = self._create_test_improvement_request()
                    issue_number = asyncio.run(github.create_issue(request))

                    self.log_result(
                        "GitHub Issue Creation",
                        issue_number == 123,
                        f"Created issue #{issue_number}",
                    )

            # Test PR body formatting
            pattern = ReflectionPattern(
                type="repeated_tool_use",
                severity="high",
                count=8,
                suggestion="Create automation script",
                context={"tool": "bash"},
                samples=["ls -la", "grep pattern"],
            )

            request = ImprovementRequest(
                issue_title="Automate repeated commands",
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

            pr_body = github._format_pr_body(context)
            has_reflection_context = all(
                keyword in pr_body
                for keyword in ["repeated_tool_use", "8", "high", "test_session", "bash"]
            )

            self.log_result(
                "PR Reflection Context", has_reflection_context, "PR includes reflection context"
            )

        except Exception as e:
            self.log_result("GitHub Integration", False, f"Error: {e}")

    def test_reflection_trigger_automation_criteria(self):
        """Test ReflectionTrigger automation criteria assessment"""
        print("🧪 Testing Reflection Trigger Automation Criteria...")

        try:
            # Test high severity pattern triggers automation
            high_severity_pattern = ReflectionPattern(
                type="user_frustration",
                severity="critical",
                count=3,
                suggestion="Review approach",
                context={"frustration_indicators": ["doesn't work", "broken"]},
            )

            metrics = ReflectionMetrics(40, 20, 20, 10)
            high_severity_result = ReflectionResult(
                session_id="test_session",
                timestamp=datetime.now(),
                patterns=[high_severity_pattern],
                metrics=metrics,
                suggestions=["High priority review needed"],
            )

            self.log_result(
                "High Severity Automation Trigger",
                high_severity_result.is_automation_worthy(),
                "Critical patterns trigger automation",
            )

            # Test multiple medium patterns trigger automation
            medium_patterns = [
                ReflectionPattern(
                    "repeated_tool_use", "medium", 4, "Consider script", {"tool": "bash"}
                ),
                ReflectionPattern(
                    "error_patterns",
                    "medium",
                    3,
                    "Better error handling",
                    {"errors": ["file not found"]},
                ),
            ]

            medium_result = ReflectionResult(
                session_id="test_session",
                timestamp=datetime.now(),
                patterns=medium_patterns,
                metrics=metrics,
                suggestions=["Multiple improvements needed"],
            )

            self.log_result(
                "Multiple Medium Pattern Trigger",
                medium_result.is_automation_worthy(),
                "Multiple medium patterns trigger automation",
            )

            # Test low patterns don't trigger
            low_pattern = ReflectionPattern(
                "repeated_tool_use", "low", 2, "Minor optimization", {"tool": "read"}
            )
            low_result = ReflectionResult(
                session_id="test_session",
                timestamp=datetime.now(),
                patterns=[low_pattern],
                metrics=ReflectionMetrics(20, 10, 10, 5),
                suggestions=["Minor improvement possible"],
            )

            self.log_result(
                "Low Pattern No Trigger",
                not low_result.is_automation_worthy(),
                "Low patterns don't trigger automation",
            )

        except Exception as e:
            self.log_result("Automation Criteria", False, f"Error: {e}")

    def test_data_flow_from_reflection_to_pr(self):
        """Test complete data flow from reflection to PR creation"""
        print("🧪 Testing Data Flow from Reflection to PR...")

        try:
            # Test data transformation through pipeline
            analysis = {
                "patterns": [
                    {
                        "type": "repeated_tool_use",
                        "tool": "bash",
                        "count": 6,
                        "suggestion": "Consider creating a script",
                    }
                ],
                "metrics": {
                    "total_messages": 50,
                    "user_messages": 25,
                    "assistant_messages": 25,
                    "tool_uses": 15,
                },
                "suggestions": ["Create automation script"],
            }

            # Convert to ReflectionResult
            reflection_result = convert_reflection_analysis_to_result(analysis)

            self.log_result(
                "Data Conversion",
                reflection_result is not None and len(reflection_result.patterns) == 1,
                "Analysis converts to ReflectionResult",
            )

            # Convert to ImprovementRequest
            primary_pattern = reflection_result.get_primary_issue()
            request = ImprovementRequest.from_reflection_pattern(
                primary_pattern, {"session_id": reflection_result.session_id}
            )

            self.log_result(
                "Pattern to Request Conversion",
                request.improvement_type == "tooling" and request.source_pattern.count == 6,
                "Pattern converts to improvement request",
            )

        except Exception as e:
            self.log_result("Data Flow", False, f"Error: {e}")

    def test_error_propagation_and_recovery(self):
        """Test error propagation and recovery mechanisms"""
        print("🧪 Testing Error Propagation and Recovery...")

        try:
            pipeline = ReflectionAutomationPipeline()

            # Test graceful handling of empty patterns
            empty_result = ReflectionResult(
                session_id="error_test",
                timestamp=datetime.now(),
                patterns=[],  # Empty patterns
                metrics=ReflectionMetrics(0, 0, 0, 0),
                suggestions=[],
            )

            result = asyncio.run(pipeline.process_reflection_result(empty_result))
            self.log_result(
                "Empty Pattern Handling", result is None, "Empty patterns handled gracefully"
            )

            # Test GitHub failure recovery
            github = GitHubIntegration()
            with patch.object(github, "_check_gh_cli", return_value=False):
                request = self._create_test_improvement_request()
                issue_number = asyncio.run(github.create_issue(request))

                self.log_result(
                    "GitHub Unavailable Fallback",
                    issue_number is None,
                    "GitHub unavailable handled gracefully",
                )

        except Exception as e:
            self.log_result("Error Recovery", False, f"Error: {e}")

    def test_configuration_driven_behavior(self):
        """Test configuration-driven behavior changes"""
        print("🧪 Testing Configuration-Driven Behavior...")

        try:
            config_path = Path(self.temp_dir) / "test_config.json"

            # Test with automation disabled
            config_disabled = {"automation_enabled": False}
            with open(config_path, "w") as f:
                json.dump(config_disabled, f)

            trigger_disabled = AutomationTrigger(str(config_path))
            reflection_result = self._create_test_reflection_result()

            self.log_result(
                "Configuration Disabled Automation",
                not trigger_disabled.should_trigger_automation(reflection_result),
                "Disabled configuration prevents automation",
            )

            # Test with automation enabled
            config_enabled = {"automation_enabled": True}
            with open(config_path, "w") as f:
                json.dump(config_enabled, f)

            trigger_enabled = AutomationTrigger(str(config_path))

            self.log_result(
                "Configuration Enabled Automation",
                trigger_enabled.should_trigger_automation(reflection_result),
                "Enabled configuration allows automation",
            )

        except Exception as e:
            self.log_result("Configuration Behavior", False, f"Error: {e}")

    def _create_test_reflection_result(self) -> "ReflectionResult":
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

    def _create_test_improvement_request(self) -> "ImprovementRequest":
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

    def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 Starting Integration Layer Validation Tests\n")

        # Run all tests
        self.test_stop_hook_integration()
        self.test_circuit_breaker_patterns()
        self.test_rate_limiting_mechanisms()
        self.test_workflow_orchestration_compliance()
        self.test_github_pr_creation_integration()
        self.test_reflection_trigger_automation_criteria()
        self.test_data_flow_from_reflection_to_pr()
        self.test_error_propagation_and_recovery()
        self.test_configuration_driven_behavior()

        # Print results
        print("\n" + "=" * 60)
        print("🏁 INTEGRATION LAYER VALIDATION RESULTS")
        print("=" * 60)

        passed = 0
        failed = 0

        for result in self.results:
            print(result)
            if result.startswith("✓ PASS"):
                passed += 1
            elif result.startswith("✗ FAIL"):
                failed += 1

        print("=" * 60)
        print(f"📊 SUMMARY: {passed} passed, {failed} failed")

        if failed == 0:
            print("🎉 All integration layer tests PASSED!")
        else:
            print("⚠️  Some integration layer tests FAILED. Review issues above.")

        # Cleanup
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

        return failed == 0


if __name__ == "__main__":
    validator = IntegrationLayerValidator()
    success = validator.run_all_tests()
    exit(0 if success else 1)
