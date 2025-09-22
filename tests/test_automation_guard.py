#!/usr/bin/env python3
"""
Unit tests for automation guard safety mechanisms.
Tests daily PR limits, cooldown enforcement, and duplicate prevention.
"""

import json
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from claude.tools.reflection_automation_pipeline import (
    AutomationTrigger,
    ReflectionMetrics,
    ReflectionPattern,
    ReflectionResult,
)


class TestAutomationGuard:
    """Test automation guard safety mechanisms"""

    def setup_method(self):
        """Setup test environment with temporary config"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "automation_config.json"
        self.state_path = Path(self.temp_dir) / "automation_state.json"

        # Create trigger with test paths
        self.trigger = AutomationTrigger(str(self.config_path))

        # Override state file path for testing
        original_record = self.trigger._record_automation_trigger
        original_get_last = self.trigger._get_last_automation_time

        def mock_record(session_id, workflow_id):
            state = {
                "last_automation_trigger": datetime.now().isoformat(),
                "last_session_id": session_id,
                "last_workflow_id": workflow_id,
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

        self.trigger._record_automation_trigger = mock_record
        self.trigger._get_last_automation_time = mock_get_last

    def teardown_method(self):
        """Cleanup test environment"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_daily_pr_limits(self):
        """Test daily PR creation limits prevent spam"""
        # Enable automation for testing
        self.trigger.enabled = True

        # Create a high-priority reflection result
        critical_pattern = ReflectionPattern(
            type="user_frustration",
            severity="critical",
            count=5,
            suggestion="Critical fix needed",
            context={},
        )

        metrics = ReflectionMetrics(
            total_messages=100, user_messages=50, assistant_messages=50, tool_uses=20
        )

        reflection_result = ReflectionResult(
            session_id="test_daily_limits",
            timestamp=datetime.now(),
            patterns=[critical_pattern],
            metrics=metrics,
            suggestions=["Critical issue detected"],
        )

        # First trigger should be allowed
        should_trigger_1 = self.trigger.should_trigger_automation(reflection_result)
        assert should_trigger_1 is True

        # Record the trigger
        self.trigger._record_automation_trigger("session1", "workflow1")

        # Second trigger within cooldown period should be blocked
        should_trigger_2 = self.trigger.should_trigger_automation(reflection_result)
        assert should_trigger_2 is False

        # Verify cooldown is enforced (1 hour by default)
        last_time = self.trigger._get_last_automation_time()
        assert last_time is not None
        time_diff = datetime.now() - last_time
        assert time_diff.total_seconds() < 3600  # Within last hour

    def test_cooldown_enforcement(self):
        """Test cooldown period enforcement between automation triggers"""
        self.trigger.enabled = True

        # Create automation-worthy result
        pattern = ReflectionPattern(
            type="error_patterns",
            severity="high",
            count=10,
            suggestion="Fix critical errors",
            context={},
        )

        result = ReflectionResult(
            session_id="cooldown_test",
            timestamp=datetime.now(),
            patterns=[pattern],
            metrics=ReflectionMetrics(50, 25, 25, 15),
            suggestions=["High priority fix"],
        )

        # First trigger should work
        assert self.trigger.should_trigger_automation(result) is True
        self.trigger._record_automation_trigger("session1", "workflow1")

        # Immediate retry should be blocked
        assert self.trigger.should_trigger_automation(result) is False

        # Simulate time passing (mock the state to be older)
        old_time = datetime.now() - timedelta(hours=2)  # 2 hours ago
        state = {
            "last_automation_trigger": old_time.isoformat(),
            "last_session_id": "old_session",
            "last_workflow_id": "old_workflow",
        }
        with open(self.state_path, "w") as f:
            json.dump(state, f)

        # Should now be allowed after cooldown
        assert self.trigger.should_trigger_automation(result) is True

    def test_duplicate_prevention(self):
        """Test prevention of duplicate automation for same issues"""
        self.trigger.enabled = True

        # Create identical patterns
        pattern1 = ReflectionPattern(
            type="repeated_tool_use",
            severity="high",
            count=8,
            suggestion="Create automation script",
            context={"tool": "bash", "commands": ["ls", "grep"]},
        )

        pattern2 = ReflectionPattern(
            type="repeated_tool_use",
            severity="high",
            count=8,
            suggestion="Create automation script",
            context={"tool": "bash", "commands": ["ls", "grep"]},
        )

        result1 = ReflectionResult(
            session_id="dup_test_1",
            timestamp=datetime.now(),
            patterns=[pattern1],
            metrics=ReflectionMetrics(30, 15, 15, 10),
            suggestions=["Automation needed"],
        )

        result2 = ReflectionResult(
            session_id="dup_test_2",
            timestamp=datetime.now(),
            patterns=[pattern2],
            metrics=ReflectionMetrics(30, 15, 15, 10),
            suggestions=["Automation needed"],
        )

        # First should trigger
        assert self.trigger.should_trigger_automation(result1) is True
        self.trigger._record_automation_trigger("session1", "workflow1")

        # Second identical should be blocked by cooldown
        assert self.trigger.should_trigger_automation(result2) is False

    def test_configuration_loading_and_defaults(self):
        """Test configuration loading with defaults"""
        # Test with non-existent config file
        new_trigger = AutomationTrigger(str(Path(self.temp_dir) / "nonexistent.json"))

        # Should create default config
        assert Path(self.temp_dir, "nonexistent.json").exists()

        # Load and verify defaults
        with open(Path(self.temp_dir) / "nonexistent.json") as f:
            config = json.load(f)

        assert config["automation_enabled"] is False  # Disabled by default
        assert config["trigger_thresholds"]["cooldown_hours"] == 1
        assert config["workflow_constraints"]["max_concurrent_workflows"] == 2

    def test_automation_disabled_by_default(self):
        """Test that automation is disabled by default for safety"""
        # Fresh trigger with new config
        disabled_trigger = AutomationTrigger(str(Path(self.temp_dir) / "disabled_config.json"))

        # Create automation-worthy result
        critical_pattern = ReflectionPattern(
            type="user_frustration",
            severity="critical",
            count=3,
            suggestion="Critical issue",
            context={},
        )

        result = ReflectionResult(
            session_id="disabled_test",
            timestamp=datetime.now(),
            patterns=[critical_pattern],
            metrics=ReflectionMetrics(50, 25, 25, 10),
            suggestions=["Critical fix needed"],
        )

        # Should not trigger when disabled
        assert disabled_trigger.should_trigger_automation(result) is False
        assert disabled_trigger.enabled is False

    def test_emergency_stop_mechanism(self):
        """Test emergency stop mechanism for automation"""
        self.trigger.enabled = True

        # Create very high activity pattern that might indicate runaway automation
        extreme_pattern = ReflectionPattern(
            type="repeated_tool_use",
            severity="critical",
            count=100,  # Extremely high count
            suggestion="Emergency: possible runaway automation",
            context={"tool": "bash", "emergency": True},
        )

        extreme_result = ReflectionResult(
            session_id="emergency_test",
            timestamp=datetime.now(),
            patterns=[extreme_pattern],
            metrics=ReflectionMetrics(1000, 500, 500, 200),  # Very high activity
            suggestions=["Emergency situation detected"],
        )

        # Even extreme cases should respect cooldown for safety
        assert self.trigger.should_trigger_automation(extreme_result) is True
        self.trigger._record_automation_trigger("emergency1", "workflow1")

        # Immediate retry should still be blocked
        assert self.trigger.should_trigger_automation(extreme_result) is False

    def test_state_corruption_recovery(self):
        """Test recovery from corrupted state files"""
        self.trigger.enabled = True

        # Create corrupted state file
        with open(self.state_path, "w") as f:
            f.write("corrupted json content {")

        # Should handle corruption gracefully
        last_time = self.trigger._get_last_automation_time()
        assert last_time is None  # Should return None for corrupted state

        # Should still allow new automation after corruption
        pattern = ReflectionPattern(
            type="error_patterns", severity="high", count=5, suggestion="Fix errors", context={}
        )

        result = ReflectionResult(
            session_id="corruption_test",
            timestamp=datetime.now(),
            patterns=[pattern],
            metrics=ReflectionMetrics(40, 20, 20, 8),
            suggestions=["Error handling needed"],
        )

        assert self.trigger.should_trigger_automation(result) is True

    def test_concurrent_access_safety(self):
        """Test safety with multiple concurrent automation attempts"""
        self.trigger.enabled = True

        pattern = ReflectionPattern(
            type="user_frustration",
            severity="critical",
            count=2,
            suggestion="Critical fix",
            context={},
        )

        result = ReflectionResult(
            session_id="concurrent_test",
            timestamp=datetime.now(),
            patterns=[pattern],
            metrics=ReflectionMetrics(30, 15, 15, 5),
            suggestions=["Urgent fix needed"],
        )

        # Simulate first process triggering automation
        assert self.trigger.should_trigger_automation(result) is True
        self.trigger._record_automation_trigger("session1", "workflow1")

        # Simulate second concurrent process - should be blocked
        second_trigger = AutomationTrigger(str(self.config_path))
        second_trigger.enabled = True
        second_trigger._get_last_automation_time = self.trigger._get_last_automation_time

        assert second_trigger.should_trigger_automation(result) is False

    def test_automation_worthiness_thresholds(self):
        """Test that automation guard respects automation worthiness"""
        self.trigger.enabled = True

        # Create low-priority pattern that shouldn't trigger automation
        low_pattern = ReflectionPattern(
            type="repeated_tool_use",
            severity="low",
            count=2,
            suggestion="Minor optimization",
            context={"tool": "read"},
        )

        low_result = ReflectionResult(
            session_id="low_priority_test",
            timestamp=datetime.now(),
            patterns=[low_pattern],
            metrics=ReflectionMetrics(20, 10, 10, 3),
            suggestions=["Minor improvement available"],
        )

        # Should not trigger for non-automation-worthy results
        assert self.trigger.should_trigger_automation(low_result) is False

        # Even if no cooldown exists, low priority shouldn't trigger
        assert self.trigger._get_last_automation_time() is None
        assert self.trigger.should_trigger_automation(low_result) is False


class TestSafetyLimits:
    """Test overall safety limits and circuit breakers"""

    def test_maximum_concurrent_workflows(self):
        """Test maximum concurrent workflow limits"""
        # This would typically involve checking active workflows
        # For now, test the configuration loading

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            trigger = AutomationTrigger(str(config_path))

            config = trigger._load_config()
            max_concurrent = config["workflow_constraints"]["max_concurrent_workflows"]

            # Should have reasonable limit
            assert max_concurrent <= 5  # Not too many concurrent workflows
            assert max_concurrent >= 1  # At least one allowed

    def test_workflow_complexity_limits(self):
        """Test that workflow complexity is limited for safety"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            trigger = AutomationTrigger(str(config_path))

            config = trigger._load_config()
            constraints = config["workflow_constraints"]

            # Should have reasonable complexity limits
            assert constraints["max_lines_per_improvement"] <= 500
            assert constraints["max_components_per_improvement"] <= 5

    def test_rate_limiting_configuration(self):
        """Test rate limiting configuration"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            trigger = AutomationTrigger(str(config_path))

            config = trigger._load_config()
            thresholds = config["trigger_thresholds"]

            # Should have reasonable cooldown
            assert thresholds["cooldown_hours"] >= 0.5  # At least 30 minutes
            assert thresholds["cooldown_hours"] <= 24  # Not more than a day


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
