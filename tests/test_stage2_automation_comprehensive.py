#!/usr/bin/env python3
"""
Comprehensive test suite for Stage 2 Automation Engine
Tests priority scoring, automation guards, workflow integration, and error handling.
"""

import json
import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import automation modules
automation_path = project_root / ".claude/tools/amplihack/automation"
sys.path.insert(0, str(automation_path))

try:
    from automation_guard import AutomationGuard
    from priority_scorer import PriorityScorer, ScoringResult
    from stage2_engine import AutomationResult, PRResult, Stage2AutomationEngine
except ImportError as e:
    pytest.skip(f"Automation modules not found: {e}", allow_module_level=True)


class TestPriorityScoring:
    """Test priority scoring system for different pattern types"""

    def setup_method(self):
        """Setup test environment"""
        self.scorer = PriorityScorer()

    def test_security_vulnerability_highest_priority(self):
        """Test that security vulnerabilities get highest base priority"""
        security_pattern = {
            "type": "security_vulnerability",
            "severity": "critical",
            "count": 1,
            "context": {"scope": "system_wide"},
            "suggestion": "Critical security fix needed",
        }

        result = self.scorer.score_pattern(security_pattern)

        assert result.score >= 150, (
            f"Security vulnerability should get critical priority, got {result.score}"
        )
        assert result.category == "critical_priority"
        assert "security_vulnerability" in result.reasoning

    def test_user_frustration_high_priority(self):
        """Test that user frustration patterns get high priority"""
        frustration_pattern = {
            "type": "user_frustration",
            "severity": "high",
            "count": 3,
            "context": {"scope": "module"},
            "suggestion": "Address user pain points",
        }

        result = self.scorer.score_pattern(frustration_pattern)

        assert result.score >= 100, f"User frustration should be high priority, got {result.score}"
        assert result.category in ["high_priority", "critical_priority"]

    def test_repeated_tool_use_medium_priority(self):
        """Test that repeated tool use gets appropriate priority based on frequency"""
        # Low frequency - should be medium/low priority
        low_frequency = {
            "type": "repeated_tool_use",
            "severity": "medium",
            "count": 3,
            "context": {"tool": "bash"},
            "suggestion": "Consider automation",
        }

        result_low = self.scorer.score_pattern(low_frequency)
        assert result_low.score < 100, (
            f"Low frequency repetition should be lower priority, got {result_low.score}"
        )

        # High frequency - should be higher priority
        high_frequency = {
            "type": "repeated_tool_use",
            "severity": "high",
            "count": 15,  # High count
            "context": {"tool": "bash"},
            "suggestion": "Automate repetitive task",
        }

        result_high = self.scorer.score_pattern(high_frequency)
        assert result_high.score > result_low.score, "Higher frequency should get higher score"
        assert result_high.score >= 80, (
            f"High frequency repetition should be medium+ priority, got {result_high.score}"
        )

    def test_documentation_gap_low_priority(self):
        """Test that documentation gaps get low priority"""
        doc_pattern = {
            "type": "documentation_gap",
            "severity": "low",
            "count": 2,
            "context": {},
            "suggestion": "Add documentation",
        }

        result = self.scorer.score_pattern(doc_pattern)

        assert result.score < 60, f"Documentation gaps should be low priority, got {result.score}"
        assert result.category in ["low_priority", "no_action"]

    def test_frequency_bonus_calculation(self):
        """Test that frequency bonuses are applied correctly"""
        base_pattern = {
            "type": "error_patterns",
            "severity": "medium",
            "context": {},
            "suggestion": "Fix errors",
        }

        # Test different frequency levels based on actual thresholds in priority_scorer.py
        frequency_tests = [
            (2, 0),  # Below threshold - no bonus
            (5, 15),  # 5-9 occurrences - 15 point bonus (matches FREQUENCY_THRESHOLDS)
            (12, 30),  # 10-19 occurrences - 30 point bonus
            (25, 50),  # 20+ occurrences - 50 point bonus
        ]

        for count, expected_bonus in frequency_tests:
            pattern = base_pattern.copy()
            pattern["count"] = count

            result = self.scorer.score_pattern(pattern)
            assert result.factors["frequency_bonus"] == expected_bonus, (
                f"Count {count} should give {expected_bonus} bonus, got {result.factors['frequency_bonus']}"
            )

    def test_severity_multipliers(self):
        """Test that severity multipliers work correctly"""
        base_pattern = {
            "type": "workflow_inefficiency",
            "count": 3,
            "context": {},
            "suggestion": "Improve workflow",
        }

        base_score = self.scorer.PRIORITY_WEIGHTS["workflow_inefficiency"]

        # Test each severity level
        severity_tests = [("low", 0.5), ("medium", 1.0), ("high", 1.5), ("critical", 2.0)]

        for severity, multiplier in severity_tests:
            pattern = base_pattern.copy()
            pattern["severity"] = severity

            result = self.scorer.score_pattern(pattern)
            expected_adjustment = int(base_score * multiplier) - base_score

            assert result.factors["severity_adjustment"] == expected_adjustment, (
                f"Severity {severity} should adjust by {expected_adjustment}, got {result.factors['severity_adjustment']}"
            )

    def test_urgency_indicators(self):
        """Test that urgency indicators add appropriate bonuses"""
        # Pattern with blocking indicator
        blocking_pattern = {
            "type": "error_patterns",
            "severity": "medium",
            "count": 3,
            "context": {"scope": "module", "blocking": True},
            "suggestion": "Fix blocking error",
        }

        result = self.scorer.score_pattern(blocking_pattern)
        assert result.factors["urgency_bonus"] >= 30, "Blocking indicator should add urgency bonus"

        # Pattern with critical path indicator
        critical_pattern = {
            "type": "performance_bottleneck",
            "severity": "medium",
            "count": 2,
            "context": {"critical_path": True},
            "suggestion": "Fix performance issue",
        }

        result = self.scorer.score_pattern(critical_pattern)
        assert result.factors["urgency_bonus"] >= 25, "Critical path should add urgency bonus"

    def test_pattern_sorting(self):
        """Test that multiple patterns are sorted correctly by priority"""
        patterns = [
            {"type": "documentation_gap", "severity": "low", "count": 1},
            {"type": "user_frustration", "severity": "critical", "count": 2},
            {"type": "repeated_tool_use", "severity": "high", "count": 8},
            {"type": "security_vulnerability", "severity": "high", "count": 1},
        ]

        scored_patterns = self.scorer.score_patterns(patterns)

        # Should be sorted by score descending
        scores = [result.score for _, result in scored_patterns]
        assert scores == sorted(scores, reverse=True), (
            "Patterns should be sorted by score descending"
        )

        # Security vulnerability and user frustration should be at top
        top_types = [pattern["type"] for pattern, _ in scored_patterns[:2]]
        assert "security_vulnerability" in top_types or "user_frustration" in top_types
        assert "documentation_gap" != scored_patterns[0][0]["type"], (
            "Documentation gap should not be highest priority"
        )


class TestAutomationGuards:
    """Test automation guard safety mechanisms"""

    def setup_method(self):
        """Setup test environment with temporary files"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "guard_config.json"
        self.state_path = Path(self.temp_dir) / "guard_state.json"

        self.guard = AutomationGuard(config_path=self.config_path, state_path=self.state_path)

        # Enable test mode to reduce cooldowns
        self.guard.config["cooldown_hours"] = 0.01  # Very short cooldown for testing

    def teardown_method(self):
        """Cleanup test environment"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_daily_pr_limits(self):
        """Test daily PR limits prevent excessive automation"""
        # Enable test mode to disable cooldowns
        with patch.dict(os.environ, {"AUTOMATION_TEST_MODE": "true"}):
            test_guard = AutomationGuard(config_path=self.config_path, state_path=self.state_path)
            # Set low limit for testing
            test_guard.config["max_prs_per_day"] = 2

            # First automation should be allowed
            should_automate_1, reason_1 = test_guard.should_automate(80, "normal_pattern")
            assert should_automate_1 is True, f"First automation should be allowed: {reason_1}"

            # Record first automation
            test_guard.record_automation_attempt(success=True, pr_number=1)

            # Second automation should be allowed
            should_automate_2, reason_2 = test_guard.should_automate(80, "normal_pattern")
            assert should_automate_2 is True, f"Second automation should be allowed: {reason_2}"

            # Record second automation
            test_guard.record_automation_attempt(success=True, pr_number=2)

            # Third automation should be blocked
            should_automate_3, reason_3 = test_guard.should_automate(80, "normal_pattern")
            assert should_automate_3 is False, "Third automation should be blocked by daily limit"
            assert "Daily PR limit" in reason_3

    def test_cooldown_enforcement(self):
        """Test cooldown periods between automations"""
        # Set short cooldown for testing
        self.guard.config["cooldown_hours"] = 1

        # First automation
        should_automate_1, _ = self.guard.should_automate(80, "test_pattern")
        assert should_automate_1 is True

        self.guard.record_automation_attempt(success=True, pr_number=1)

        # Immediate retry should be blocked
        should_automate_2, reason_2 = self.guard.should_automate(80, "test_pattern")
        assert should_automate_2 is False
        assert "Cooldown period" in reason_2

        # Simulate time passing by manually updating state
        old_time = datetime.now() - timedelta(hours=2)
        self.guard.state["last_pr_timestamp"] = old_time.isoformat()

        # Should now be allowed after cooldown
        should_automate_3, reason_3 = self.guard.should_automate(80, "test_pattern")
        assert should_automate_3 is True, f"Should be allowed after cooldown: {reason_3}"

    def test_score_thresholds(self):
        """Test that score thresholds are enforced"""
        min_threshold = self.guard.config["min_score_threshold"]

        # Score below threshold should be rejected
        low_score = min_threshold - 10
        should_automate, reason = self.guard.should_automate(low_score, "test_pattern")
        assert should_automate is False
        assert "below minimum threshold" in reason

        # Score at threshold should be allowed
        threshold_score = min_threshold
        should_automate, _ = self.guard.should_automate(threshold_score, "test_pattern")
        assert should_automate is True

        # Critical override should work even below threshold
        critical_score = self.guard.config["critical_override_threshold"]
        should_automate, _ = self.guard.should_automate(critical_score, "test_pattern")
        assert should_automate is True

    def test_blacklisted_patterns(self):
        """Test that blacklisted patterns are blocked"""
        blacklisted_patterns = [
            "database_migration",
            "authentication_change",
            "payment_processing",
            "user_data_handling",
            "deployment_config",
        ]

        for pattern_type in blacklisted_patterns:
            should_automate, reason = self.guard.should_automate(150, pattern_type)  # High score
            assert should_automate is False, f"Blacklisted pattern {pattern_type} should be blocked"
            assert "blacklisted" in reason.lower()

    def test_failed_attempts_limit(self):
        """Test that too many failed attempts trigger safety stop"""
        max_failed = self.guard.config["max_failed_attempts"]

        # Record maximum failed attempts
        for i in range(max_failed):
            self.guard.record_automation_attempt(success=False, error=f"Test error {i}")

        # Next automation should be blocked
        should_automate, reason = self.guard.should_automate(100, "test_pattern")
        assert should_automate is False
        assert "failed attempts" in reason.lower()

        # Reset should allow automation again
        self.guard.reset_failed_attempts()
        should_automate, _ = self.guard.should_automate(100, "test_pattern")
        assert should_automate is True

    def test_context_guards(self):
        """Test context-specific guard rules"""
        # Test CI environment blocking
        ci_context = {"ci_environment": True}
        should_automate, reason = self.guard.should_automate(80, "test_pattern", ci_context)
        assert should_automate is False
        assert "CI environment" in reason

        # Test user approval requirement
        no_approval_context = {"user_approved": False}
        should_automate, reason = self.guard.should_automate(
            80, "test_pattern", no_approval_context
        )
        assert should_automate is False
        assert "not approved" in reason

    def test_environment_overrides(self):
        """Test environment variable overrides for testing"""
        # Test automation disabled override
        with patch.dict(os.environ, {"AUTOMATION_DISABLED": "true"}):
            guard = AutomationGuard(config_path=self.config_path, state_path=self.state_path)
            assert guard.config["max_prs_per_day"] == 0

        # Test test mode override
        with patch.dict(os.environ, {"AUTOMATION_TEST_MODE": "true"}):
            guard = AutomationGuard(config_path=self.config_path, state_path=self.state_path)
            assert guard.config["cooldown_hours"] == 0
            assert guard.config["min_score_threshold"] == 0


class TestStage2AutomationEngine:
    """Test the main Stage2AutomationEngine"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        config_path = Path(self.temp_dir) / "engine_config.json"

        # Use test mode environment for consistent testing
        with patch.dict(os.environ, {"AUTOMATION_TEST_MODE": "true"}):
            self.engine = Stage2AutomationEngine(config_path=config_path)

        # Reset state for clean tests
        self.engine.guard.state["daily_pr_count"] = 0
        self.engine.guard.state["weekly_pr_count"] = 0
        self.engine.guard.state["failed_attempts"] = 0

    def teardown_method(self):
        """Cleanup test environment"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_analysis(self, pattern_type="user_frustration", severity="high", count=3):
        """Create test reflection analysis file"""
        analysis = {
            "session_id": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "patterns": [
                {
                    "type": pattern_type,
                    "severity": severity,
                    "count": count,
                    "suggestion": f"Fix {pattern_type}",
                    "context": {"scope": "module"},
                    "confidence": 0.9,
                }
            ],
            "metrics": {
                "total_messages": 50,
                "user_messages": 25,
                "assistant_messages": 25,
                "tool_uses": 15,
            },
            "suggestions": ["Automation needed"],
        }

        analysis_file = Path(self.temp_dir) / "test_analysis.json"
        with open(analysis_file, "w") as f:
            json.dump(analysis, f, indent=2)

        return analysis_file

    def test_reflection_processing_success(self):
        """Test successful processing of reflection insights"""
        # Create high-priority analysis
        analysis_file = self.create_test_analysis("user_frustration", "critical", 5)

        # Mock the workflow execution to return success
        with patch.object(self.engine, "execute_improvement_workflow") as mock_workflow:
            mock_pr = PRResult(
                pr_number=123,
                pr_url="https://github.com/test/repo/pull/123",
                branch_name="auto-improve/test_branch",
                title="Test automation PR",
                status="ready",
            )
            mock_workflow.return_value = mock_pr

            result = self.engine.process_reflection_insights(analysis_file)

            assert result.success is True
            assert result.pr_number == 123
            assert result.pattern_type == "user_frustration"
            assert "Successfully created PR" in result.message

    def test_reflection_processing_low_priority(self):
        """Test that low-priority patterns don't trigger automation"""
        # Create low-priority analysis
        analysis_file = self.create_test_analysis("documentation_gap", "low", 1)

        result = self.engine.process_reflection_insights(analysis_file)

        assert result.success is False
        assert "too low for automation" in result.message or "not triggered" in result.message

    def test_pr_creation_decision_logic(self):
        """Test the decision logic for PR creation"""
        # High priority patterns should trigger PR creation
        high_priority_patterns = [
            {"type": "user_frustration", "severity": "critical", "count": 3, "confidence": 0.9}
        ]

        should_create, reason = self.engine.should_create_pr(high_priority_patterns)
        assert should_create is True, f"High priority should trigger PR: {reason}"

        # Low confidence patterns should not trigger PR creation
        low_confidence_patterns = [
            {"type": "user_frustration", "severity": "high", "count": 3, "confidence": 0.5}
        ]

        should_create, reason = self.engine.should_create_pr(low_confidence_patterns)
        assert should_create is False
        assert "confidence too low" in reason

        # Empty patterns should not trigger PR creation
        should_create, reason = self.engine.should_create_pr([])
        assert should_create is False
        assert "No patterns" in reason

    def test_workflow_execution_with_agent(self):
        """Test workflow execution using improvement-workflow agent"""
        self.engine.config["use_improvement_workflow_agent"] = True

        pattern = {"type": "repeated_tool_use", "severity": "high", "count": 10}

        # Mock agent existence and execution
        with patch("pathlib.Path.exists", return_value=True):
            with patch.object(self.engine, "_mock_pr_result") as mock_pr:
                expected_pr = PRResult(
                    pr_number=456,
                    pr_url="https://github.com/test/repo/pull/456",
                    branch_name="auto-improve/workflow_123",
                    title="Test agent PR",
                    status="draft",
                )
                mock_pr.return_value = expected_pr

                result = self.engine.execute_improvement_workflow(pattern)

                assert result is not None
                assert result.pr_number == 456
                assert "auto-improve" in result.branch_name

    def test_error_handling_invalid_analysis(self):
        """Test error handling with invalid analysis files"""
        # Test missing file
        missing_file = Path(self.temp_dir) / "missing.json"
        result = self.engine.process_reflection_insights(missing_file)
        assert result.success is False
        assert "not found" in result.message

        # Test corrupted JSON
        corrupted_file = Path(self.temp_dir) / "corrupted.json"
        with open(corrupted_file, "w") as f:
            f.write("invalid json {")

        result = self.engine.process_reflection_insights(corrupted_file)
        assert result.success is False
        assert "error" in result.message.lower()

    def test_engine_status_reporting(self):
        """Test engine status reporting"""
        status = self.engine.get_status()

        # Should have expected status fields
        assert "engine_enabled" in status
        assert "guard_status" in status
        assert "recent_workflows" in status
        assert "active_workflows" in status
        assert "config" in status

        # Guard status should be included
        assert isinstance(status["guard_status"], dict)
        assert "automation_enabled" in status["guard_status"]

    def test_configuration_changes(self):
        """Test that configuration changes affect behavior"""
        # Disable automation in config
        self.engine.config["automation_enabled"] = False

        patterns = [{"type": "user_frustration", "severity": "critical", "count": 5}]
        should_create, reason = self.engine.should_create_pr(patterns)

        assert should_create is False
        assert "disabled" in reason

        # Re-enable automation
        self.engine.config["automation_enabled"] = True
        should_create, reason = self.engine.should_create_pr(patterns)
        assert should_create is True


class TestIntegration:
    """Test full integration across all components"""

    def setup_method(self):
        """Setup integrated test environment"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Cleanup test environment"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_high_priority_automation_flow(self):
        """Test complete flow for high-priority patterns"""
        # Create components with test mode
        config_path = Path(self.temp_dir) / "engine_config.json"
        with patch.dict(os.environ, {"AUTOMATION_TEST_MODE": "true"}):
            engine = Stage2AutomationEngine(config_path=config_path)

        # Reset state for clean test
        engine.guard.state["daily_pr_count"] = 0
        engine.guard.state["weekly_pr_count"] = 0
        engine.guard.state["failed_attempts"] = 0

        # Create high-priority reflection analysis
        analysis = {
            "session_id": "integration_test_high",
            "timestamp": datetime.now().isoformat(),
            "patterns": [
                {
                    "type": "security_vulnerability",
                    "severity": "critical",
                    "count": 2,
                    "suggestion": "Critical security fix needed",
                    "context": {"scope": "system_wide", "blocking": True},
                    "confidence": 0.95,
                }
            ],
            "metrics": {
                "total_messages": 80,
                "user_messages": 40,
                "assistant_messages": 40,
                "tool_uses": 20,
            },
            "suggestions": ["Immediate security fix required"],
        }

        analysis_file = Path(self.temp_dir) / "high_priority_analysis.json"
        with open(analysis_file, "w") as f:
            json.dump(analysis, f, indent=2)

        # Mock workflow execution
        with patch.object(engine, "execute_improvement_workflow") as mock_workflow:
            mock_pr = PRResult(
                pr_number=789,
                pr_url="https://github.com/test/repo/pull/789",
                branch_name="auto-improve/security_fix",
                title="Critical security fix",
                status="ready",
            )
            mock_workflow.return_value = mock_pr

            result = engine.process_reflection_insights(analysis_file)

            # Verify automation was triggered
            assert result.success is True
            assert result.pr_number == 789
            assert result.pattern_type == "security_vulnerability"
            assert result.score >= 150  # Should be critical priority

    def test_rate_limiting_prevents_spam(self):
        """Test that rate limiting prevents automation spam"""
        # Create engine with strict limits
        config_path = Path(self.temp_dir) / "strict_config.json"
        strict_config = {
            "automation_enabled": True,
            "use_improvement_workflow_agent": False,
            "max_retries": 1,
        }
        with open(config_path, "w") as f:
            json.dump(strict_config, f)

        with patch.dict(os.environ, {"AUTOMATION_TEST_MODE": "false"}):  # Test with normal limits
            engine = Stage2AutomationEngine(config_path=config_path)

        # Set strict guard limits
        engine.guard.config["max_prs_per_day"] = 1
        engine.guard.config["cooldown_hours"] = 24
        # Reset all state for clean test
        engine.guard.state["daily_pr_count"] = 0
        engine.guard.state["weekly_pr_count"] = 0
        engine.guard.state["failed_attempts"] = 0
        engine.guard.state["last_pr_timestamp"] = None  # Clear last PR timestamp

        # Create automation-worthy analysis
        analysis_file = Path(self.temp_dir) / "rate_limit_analysis.json"
        analysis = {
            "session_id": "rate_limit_test",
            "timestamp": datetime.now().isoformat(),
            "patterns": [
                {
                    "type": "user_frustration",
                    "severity": "critical",
                    "count": 5,
                    "suggestion": "Fix user issues",
                    "context": {"scope": "module"},
                    "confidence": 0.9,
                }
            ],
            "metrics": {
                "total_messages": 60,
                "user_messages": 30,
                "assistant_messages": 30,
                "tool_uses": 12,
            },
            "suggestions": ["User experience improvement needed"],
        }

        with open(analysis_file, "w") as f:
            json.dump(analysis, f, indent=2)

        # Mock successful first workflow
        with patch.object(engine, "execute_improvement_workflow") as mock_workflow:
            mock_pr = PRResult(
                pr_number=101,
                pr_url="https://github.com/test/repo/pull/101",
                branch_name="auto-improve/first",
                title="First automation",
                status="ready",
            )
            mock_workflow.return_value = mock_pr

            # First automation should succeed
            result1 = engine.process_reflection_insights(analysis_file)
            assert result1.success is True

            # Immediate second automation should be blocked
            result2 = engine.process_reflection_insights(analysis_file)
            assert result2.success is False
            assert "limit" in result2.message.lower() or "cooldown" in result2.message.lower()

    def test_failed_automation_recovery(self):
        """Test recovery from failed automation attempts"""
        config_path = Path(self.temp_dir) / "recovery_config.json"
        with patch.dict(os.environ, {"AUTOMATION_TEST_MODE": "true"}):
            engine = Stage2AutomationEngine(config_path=config_path)

        # Reset state for clean test
        engine.guard.state["daily_pr_count"] = 0
        engine.guard.state["weekly_pr_count"] = 0
        engine.guard.state["failed_attempts"] = 0

        # Create analysis
        analysis_file = Path(self.temp_dir) / "recovery_analysis.json"
        analysis = {
            "session_id": "recovery_test",
            "timestamp": datetime.now().isoformat(),
            "patterns": [
                {
                    "type": "error_patterns",
                    "severity": "high",
                    "count": 7,
                    "suggestion": "Fix error handling",
                    "context": {"scope": "component"},
                    "confidence": 0.85,
                }
            ],
            "metrics": {
                "total_messages": 45,
                "user_messages": 23,
                "assistant_messages": 22,
                "tool_uses": 8,
            },
            "suggestions": ["Error handling improvement needed"],
        }

        with open(analysis_file, "w") as f:
            json.dump(analysis, f, indent=2)

        # Mock failed workflow execution
        with patch.object(engine, "execute_improvement_workflow", return_value=None):
            result = engine.process_reflection_insights(analysis_file)

            # Should handle failure gracefully
            assert result.success is False
            assert "failed" in result.message.lower()
            assert result.pattern_type == "error_patterns"
            assert result.pr_number is None

        # Verify failure was recorded in guard
        guard_status = engine.guard.get_current_status()
        assert guard_status["failed_attempts"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
