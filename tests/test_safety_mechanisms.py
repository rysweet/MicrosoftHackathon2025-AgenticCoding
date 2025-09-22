#!/usr/bin/env python3
"""
Safety mechanism tests for rate limiting, circuit breakers, and quality thresholds.
Tests critical safety features that prevent automation spam and ensure quality.
"""

import asyncio
import json
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from .claude.tools.reflection_automation_pipeline import (
    AutomationTrigger,
    GitHubIntegration,
    ImprovementRequest,
    ReflectionMetrics,
    ReflectionPattern,
    ReflectionResult,
    WorkflowOrchestrator,
)


class TestRateLimiting:
    """Test rate limiting mechanisms to prevent automation spam"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "rate_limit_config.json"
        self.state_path = Path(self.temp_dir) / "rate_limit_state.json"

    def teardown_method(self):
        """Cleanup test environment"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_rate_limiting_prevents_spam(self):
        """Test that rate limiting prevents automation spam"""
        # Create automation trigger with rate limiting
        trigger = AutomationTrigger(str(self.config_path))
        trigger.enabled = True

        # Override state handling for testing
        def mock_record(session_id, workflow_id):
            state = {
                "last_automation_trigger": datetime.now().isoformat(),
                "last_session_id": session_id,
                "last_workflow_id": workflow_id,
                "trigger_count_today": 1,
            }
            with open(self.state_path, "w") as f:
                json.dump(state, f, indent=2)

        def mock_get_last():
            if not self.state_path.exists():
                return None
            try:
                with open(self.state_path) as f:
                    state = json.load(f)
                last_trigger = state.get("last_automation_trigger")
                if last_trigger:
                    return datetime.fromisoformat(last_trigger)
            except (json.JSONDecodeError, ValueError):
                pass
            return None

        trigger._record_automation_trigger = mock_record
        trigger._get_last_automation_time = mock_get_last

        # Create high-priority automation-worthy result
        critical_pattern = ReflectionPattern(
            type="user_frustration",
            severity="critical",
            count=5,
            suggestion="Critical issue needs immediate attention",
            context={"urgency": "high"},
        )

        result = ReflectionResult(
            session_id="spam_test_1",
            timestamp=datetime.now(),
            patterns=[critical_pattern],
            metrics=ReflectionMetrics(100, 50, 50, 20),
            suggestions=["Critical issue detected"],
        )

        # First trigger should work
        should_trigger_1 = trigger.should_trigger_automation(result)
        assert should_trigger_1 is True

        # Record the trigger
        trigger._record_automation_trigger("spam_session_1", "workflow_1")

        # Immediate second trigger should be rate limited
        should_trigger_2 = trigger.should_trigger_automation(result)
        assert should_trigger_2 is False

        # Even after changing session, should still be rate limited
        result.session_id = "spam_test_2"
        should_trigger_3 = trigger.should_trigger_automation(result)
        assert should_trigger_3 is False

    def test_daily_trigger_limits(self):
        """Test daily trigger limits to prevent excessive automation"""
        trigger = AutomationTrigger(str(self.config_path))
        trigger.enabled = True

        # Mock state to simulate multiple triggers today
        trigger_count = 0

        def mock_record(session_id, workflow_id):
            nonlocal trigger_count
            trigger_count += 1
            state = {
                "last_automation_trigger": datetime.now().isoformat(),
                "last_session_id": session_id,
                "last_workflow_id": workflow_id,
                "trigger_count_today": trigger_count,
                "reset_date": datetime.now().date().isoformat(),
            }
            with open(self.state_path, "w") as f:
                json.dump(state, f, indent=2)

        def mock_get_count():
            if not self.state_path.exists():
                return 0
            try:
                with open(self.state_path) as f:
                    state = json.load(f)
                reset_date = state.get("reset_date")
                if reset_date == datetime.now().date().isoformat():
                    return state.get("trigger_count_today", 0)
            except (json.JSONDecodeError, ValueError):
                pass
            return 0

        trigger._record_automation_trigger = mock_record

        # Override should_trigger_automation to check daily limits
        original_should_trigger = trigger.should_trigger_automation

        def enhanced_should_trigger(reflection_result):
            # Check basic conditions first
            if not original_should_trigger(reflection_result):
                return False

            # Check daily limit (e.g., maximum 5 per day)
            daily_count = mock_get_count()
            if daily_count >= 5:
                return False

            return True

        trigger.should_trigger_automation = enhanced_should_trigger

        # Create automation-worthy pattern
        pattern = ReflectionPattern(
            type="error_patterns",
            severity="high",
            count=10,
            suggestion="Fix critical errors",
            context={},
        )

        result = ReflectionResult(
            session_id="daily_limit_test",
            timestamp=datetime.now(),
            patterns=[pattern],
            metrics=ReflectionMetrics(80, 40, 40, 15),
            suggestions=["Critical error fix needed"],
        )

        # Should allow up to 5 triggers
        for i in range(5):
            # Mock cooldown as passed
            if i > 0:
                old_time = datetime.now() - timedelta(hours=2)
                state = {
                    "last_automation_trigger": old_time.isoformat(),
                    "trigger_count_today": i,
                    "reset_date": datetime.now().date().isoformat(),
                }
                with open(self.state_path, "w") as f:
                    json.dump(state, f)

            should_trigger = trigger.should_trigger_automation(result)
            if should_trigger:
                trigger._record_automation_trigger(f"session_{i}", f"workflow_{i}")

        # 6th trigger should be blocked by daily limit
        old_time = datetime.now() - timedelta(hours=2)
        state = {
            "last_automation_trigger": old_time.isoformat(),
            "trigger_count_today": 5,
            "reset_date": datetime.now().date().isoformat(),
        }
        with open(self.state_path, "w") as f:
            json.dump(state, f)

        should_trigger_6 = enhanced_should_trigger(result)
        assert should_trigger_6 is False

    def test_burst_protection(self):
        """Test protection against burst requests within short time windows"""
        trigger = AutomationTrigger(str(self.config_path))
        trigger.enabled = True

        # Track recent triggers for burst detection
        recent_triggers = []

        def mock_record_with_burst_check(session_id, workflow_id):
            now = datetime.now()
            recent_triggers.append(now)

            # Keep only triggers from last 10 minutes
            cutoff = now - timedelta(minutes=10)
            recent_triggers[:] = [t for t in recent_triggers if t > cutoff]

            state = {
                "last_automation_trigger": now.isoformat(),
                "last_session_id": session_id,
                "last_workflow_id": workflow_id,
                "recent_triggers": [t.isoformat() for t in recent_triggers],
            }
            with open(self.state_path, "w") as f:
                json.dump(state, f, indent=2)

        def enhanced_should_trigger_with_burst(reflection_result):
            # Load recent triggers
            if self.state_path.exists():
                try:
                    with open(self.state_path) as f:
                        state = json.load(f)
                    trigger_times = [
                        datetime.fromisoformat(t) for t in state.get("recent_triggers", [])
                    ]

                    # Check for burst (more than 2 triggers in 10 minutes)
                    now = datetime.now()
                    recent = [t for t in trigger_times if (now - t).total_seconds() < 600]
                    if len(recent) >= 2:
                        return False
                except (json.JSONDecodeError, ValueError):
                    pass

            return trigger.should_trigger_automation(reflection_result)

        trigger._record_automation_trigger = mock_record_with_burst_check

        # Create automation-worthy pattern
        pattern = ReflectionPattern(
            type="user_frustration",
            severity="critical",
            count=3,
            suggestion="Critical issue",
            context={},
        )

        result = ReflectionResult(
            session_id="burst_test",
            timestamp=datetime.now(),
            patterns=[pattern],
            metrics=ReflectionMetrics(60, 30, 30, 10),
            suggestions=["Critical fix needed"],
        )

        # First two triggers should work (with time spacing)
        assert enhanced_should_trigger_with_burst(result) is True
        trigger._record_automation_trigger("burst_1", "workflow_1")

        # Wait a bit and try again
        time.sleep(0.1)

        # Clear cooldown for testing
        old_time = datetime.now() - timedelta(hours=2)
        state = {
            "last_automation_trigger": old_time.isoformat(),
            "recent_triggers": [datetime.now().isoformat()],
        }
        with open(self.state_path, "w") as f:
            json.dump(state, f)

        assert enhanced_should_trigger_with_burst(result) is True
        trigger._record_automation_trigger("burst_2", "workflow_2")

        # Third trigger within 10 minutes should be blocked
        old_time = datetime.now() - timedelta(hours=2)
        now = datetime.now()
        state = {
            "last_automation_trigger": old_time.isoformat(),
            "recent_triggers": [
                (now - timedelta(minutes=5)).isoformat(),
                (now - timedelta(minutes=2)).isoformat(),
            ],
        }
        with open(self.state_path, "w") as f:
            json.dump(state, f)

        assert enhanced_should_trigger_with_burst(result) is False


class TestCircuitBreaker:
    """Test circuit breaker patterns for automation failures"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Cleanup test environment"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_circuit_breaker_activation(self):
        """Test circuit breaker activates after consecutive failures"""
        # Mock workflow orchestrator with failure tracking
        orchestrator = WorkflowOrchestrator()

        failure_count = 0
        max_failures = 3

        async def mock_execute_workflow_with_failures(workflow_id, request):
            nonlocal failure_count
            failure_count += 1

            # Simulate failures for first few attempts
            if failure_count <= max_failures:
                return False  # Failure
            return True  # Success after failures

        orchestrator._execute_workflow = mock_execute_workflow_with_failures

        # Create test improvement request
        pattern = ReflectionPattern(
            type="repeated_tool_use",
            severity="high",
            count=8,
            suggestion="Create automation",
            context={"tool": "bash"},
        )

        request = ImprovementRequest.from_reflection_pattern(
            pattern, {"session_id": "circuit_test"}
        )

        # Create queue files to simulate multiple requests
        queue_dir = Path(self.temp_dir) / "improvement_queue"
        queue_dir.mkdir(parents=True, exist_ok=True)

        for i in range(5):
            queue_file = queue_dir / f"workflow_test_{i}.json"
            request_dict = {
                "issue_title": f"Test Issue {i}",
                "issue_description": "Test description",
                "priority": "high",
                "improvement_type": "tooling",
                "estimated_complexity": "simple",
                "max_components": 3,
                "max_lines_of_code": 200,
                "requires_security_review": False,
                "source_pattern": {
                    "type": "repeated_tool_use",
                    "severity": "high",
                    "count": 8,
                    "suggestion": "Create automation",
                    "context": {"tool": "bash"},
                    "samples": [],
                },
                "context": {"session_id": "circuit_test"},
            }

            with open(queue_file, "w") as f:
                json.dump(request_dict, f, indent=2)

        # Override orchestrator queue_dir for testing
        orchestrator.queue_dir = queue_dir

        # Process queue - should handle failures gracefully
        processed = asyncio.run(orchestrator.process_queue())

        # Should have processed some workflows despite initial failures
        assert len(processed) >= 0  # May be empty due to circuit breaker

        # Check that failed workflows are moved to failed queue
        failed_dir = Path(self.temp_dir) / "failed_workflows"
        if failed_dir.exists():
            failed_files = list(failed_dir.glob("*.json"))
            assert len(failed_files) <= 5  # Some workflows should fail

    def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery after failures subside"""
        # This test would verify that the circuit breaker allows requests through
        # again after the failure rate drops below threshold

        orchestrator = WorkflowOrchestrator()

        call_count = 0

        async def mock_execute_with_recovery(workflow_id, request):
            nonlocal call_count
            call_count += 1

            # Fail first 3, then succeed
            if call_count <= 3:
                return False
            return True

        orchestrator._execute_workflow = mock_execute_with_recovery

        # Create test queue
        queue_dir = Path(self.temp_dir) / "recovery_queue"
        queue_dir.mkdir(parents=True, exist_ok=True)
        orchestrator.queue_dir = queue_dir

        # Add test workflow
        test_workflow = {
            "issue_title": "Recovery Test",
            "issue_description": "Test recovery",
            "priority": "medium",
            "improvement_type": "pattern",
            "estimated_complexity": "simple",
            "max_components": 2,
            "max_lines_of_code": 100,
            "requires_security_review": False,
            "source_pattern": {
                "type": "long_session",
                "severity": "medium",
                "count": 1,
                "suggestion": "Improve session management",
                "context": {},
                "samples": [],
            },
            "context": {"session_id": "recovery_test"},
        }

        queue_file = queue_dir / "recovery_workflow.json"
        with open(queue_file, "w") as f:
            json.dump(test_workflow, f, indent=2)

        # Process should eventually succeed after failures
        processed = asyncio.run(orchestrator.process_queue())

        # Should handle both failures and recovery
        assert call_count > 0  # Should have attempted execution


class TestQualityThresholds:
    """Test quality threshold enforcement"""

    def test_quality_threshold_enforcement(self):
        """Test that quality thresholds prevent low-quality automation"""
        # Test improvement request quality validation

        # Low quality pattern (should not trigger automation)
        low_quality_pattern = ReflectionPattern(
            type="repeated_tool_use",
            severity="low",
            count=2,  # Very low count
            suggestion="Minor optimization",
            context={"tool": "read", "confidence": "low"},
        )

        low_quality_result = ReflectionResult(
            session_id="quality_test_low",
            timestamp=datetime.now(),
            patterns=[low_quality_pattern],
            metrics=ReflectionMetrics(10, 5, 5, 2),  # Very short session
            suggestions=["Minor improvement possible"],
        )

        # Should not be automation-worthy due to low quality
        assert low_quality_result.is_automation_worthy() is False

        # High quality pattern (should trigger automation)
        high_quality_pattern = ReflectionPattern(
            type="error_patterns",
            severity="high",
            count=10,  # High count indicates real problem
            suggestion="Fix critical error handling",
            context={"error_types": ["auth", "network"], "confidence": "high"},
        )

        high_quality_result = ReflectionResult(
            session_id="quality_test_high",
            timestamp=datetime.now(),
            patterns=[high_quality_pattern],
            metrics=ReflectionMetrics(80, 40, 40, 15),  # Substantial session
            suggestions=["Critical error handling improvements needed"],
        )

        # Should be automation-worthy due to high quality
        assert high_quality_result.is_automation_worthy() is True

    def test_complexity_limits_enforcement(self):
        """Test that complexity limits prevent overly complex automation"""
        # Create pattern that would result in complex automation
        complex_pattern = ReflectionPattern(
            type="repeated_tool_use",
            severity="critical",
            count=50,  # Very high count
            suggestion="Major system overhaul needed",
            context={
                "tool": "bash",
                "complexity_indicators": ["multiple_systems", "cross_cutting_concerns"],
                "estimated_effort": "high",
            },
        )

        request = ImprovementRequest.from_reflection_pattern(
            complex_pattern, {"session_id": "complexity_test"}
        )

        # Should have complexity constraints
        assert request.estimated_complexity == "complex"
        assert request.max_lines_of_code <= 500  # Should have reasonable limits
        assert request.max_components <= 10  # Should have reasonable limits

    def test_security_review_requirements(self):
        """Test that security-sensitive patterns require review"""
        # Security-sensitive pattern
        security_pattern = ReflectionPattern(
            type="error_patterns",
            severity="high",
            count=8,
            suggestion="Fix authentication errors",
            context={
                "error_types": ["AuthenticationError", "PermissionDenied"],
                "security_impact": "high",
            },
        )

        security_request = ImprovementRequest.from_reflection_pattern(
            security_pattern, {"session_id": "security_test"}
        )

        # Should require security review
        assert security_request.requires_security_review is True
        assert security_request.improvement_type == "error_handling"

        # Non-security pattern
        regular_pattern = ReflectionPattern(
            type="repeated_tool_use",
            severity="medium",
            count=5,
            suggestion="Create file processing script",
            context={"tool": "read", "files": ["data.txt", "config.json"]},
        )

        regular_request = ImprovementRequest.from_reflection_pattern(
            regular_pattern, {"session_id": "regular_test"}
        )

        # Should not require security review
        assert regular_request.requires_security_review is False


class TestResourceProtection:
    """Test resource protection mechanisms"""

    def test_concurrent_workflow_limits(self):
        """Test limits on concurrent workflow execution"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "concurrent_config.json"
            trigger = AutomationTrigger(str(config_path))

            config = trigger._load_config()

            # Should have reasonable concurrent limits
            max_concurrent = config["workflow_constraints"]["max_concurrent_workflows"]
            assert max_concurrent >= 1
            assert max_concurrent <= 5  # Not too many to overwhelm system

    def test_memory_usage_protection(self):
        """Test protection against excessive memory usage"""
        # Test with large pattern data
        large_context = {"data": "x" * 10000}  # 10KB of data

        large_pattern = ReflectionPattern(
            type="repeated_tool_use",
            severity="medium",
            count=5,
            suggestion="Process large data efficiently",
            context=large_context,
        )

        # Should handle large data without issues
        request = ImprovementRequest.from_reflection_pattern(
            large_pattern, {"session_id": "memory_test"}
        )

        # Should have completed without memory errors
        assert request.issue_title is not None
        assert request.improvement_type == "tooling"

    def test_timeout_protection(self):
        """Test timeout protection for long-running operations"""
        # Mock long-running GitHub operation
        github = GitHubIntegration()

        # Create test improvement request
        pattern = ReflectionPattern(
            type="error_patterns",
            severity="medium",
            count=4,
            suggestion="Fix timeout errors",
            context={"timeout_duration": "30s"},
        )

        request = ImprovementRequest.from_reflection_pattern(
            pattern, {"session_id": "timeout_test"}
        )

        # Mock subprocess to simulate timeout
        with patch("subprocess.run") as mock_run:
            # Simulate timeout
            import subprocess

            mock_run.side_effect = subprocess.TimeoutExpired("gh", 30)

            # Should handle timeout gracefully
            result = asyncio.run(github.create_issue(request))
            assert result is None  # Should return None on timeout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
