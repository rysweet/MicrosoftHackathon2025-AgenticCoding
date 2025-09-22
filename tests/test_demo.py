#!/usr/bin/env python3
"""
Demo test file to validate test infrastructure functionality.
Shows key test patterns for reflection automation system.
"""

from datetime import datetime, timedelta

import pytest


class TestReflectionPatterns:
    """Demonstrate key reflection pattern testing"""

    def test_user_frustration_detection(self):
        """Test detection of user frustration patterns in session data"""
        # Sample session data with frustration indicators
        messages = [
            {"role": "user", "content": "This doesn't work"},
            {"role": "user", "content": "Still failing"},
            {"role": "user", "content": "I'm confused why this isn't working"},
        ]

        # Mock pattern detection
        frustration_keywords = ["doesn't work", "failing", "confused", "isn't working"]
        frustration_count = 0

        for msg in messages:
            content = msg.get("content", "").lower()
            if any(keyword in content for keyword in frustration_keywords):
                frustration_count += 1

        # Should detect multiple frustration indicators
        assert frustration_count >= 2
        assert frustration_count == 3  # All three messages contain frustration

    def test_repeated_tool_pattern_detection(self):
        """Test detection of repeated tool usage patterns"""
        # Sample messages with repeated bash usage
        messages = [
            {"role": "assistant", "content": '<function_calls><invoke name="Bash">'},
            {"role": "assistant", "content": '<function_calls><invoke name="Bash">'},
            {"role": "assistant", "content": '<function_calls><invoke name="Bash">'},
            {"role": "assistant", "content": '<function_calls><invoke name="Bash">'},
            {"role": "assistant", "content": '<function_calls><invoke name="Bash">'},
        ]

        # Count bash tool usage
        bash_count = 0
        for msg in messages:
            content = msg.get("content", "")
            if "Bash" in content:
                bash_count += 1

        # Should detect repeated usage
        assert bash_count >= 3  # Threshold for automation trigger
        assert bash_count == 5  # Actual count

    def test_automation_worthiness_logic(self):
        """Test logic for determining if patterns warrant automation"""
        # High severity pattern
        high_severity_patterns = [{"type": "user_frustration", "severity": "critical", "count": 3}]

        # Multiple medium patterns
        medium_patterns = [
            {"type": "repeated_tool_use", "severity": "medium", "count": 5},
            {"type": "error_patterns", "severity": "medium", "count": 4},
        ]

        # Single low pattern
        low_patterns = [{"type": "repeated_tool_use", "severity": "low", "count": 2}]

        # Test automation worthiness
        def is_automation_worthy(patterns):
            high_severity = any(p["severity"] in ["high", "critical"] for p in patterns)
            multiple_medium = sum(1 for p in patterns if p["severity"] == "medium") >= 2
            return high_severity or multiple_medium

        assert is_automation_worthy(high_severity_patterns) is True
        assert is_automation_worthy(medium_patterns) is True
        assert is_automation_worthy(low_patterns) is False


class TestSafetyMechanisms:
    """Test critical safety mechanisms"""

    def test_rate_limiting_logic(self):
        """Test rate limiting prevents automation spam"""
        # Mock automation state
        last_trigger_time = datetime.now()
        cooldown_hours = 1

        def should_trigger_with_cooldown(current_time):
            time_diff = (current_time - last_trigger_time).total_seconds()
            return time_diff >= (cooldown_hours * 3600)

        # Test immediate retry (should be blocked)
        immediate_retry = datetime.now()
        assert should_trigger_with_cooldown(immediate_retry) is False

        # Test after cooldown period (should be allowed)
        after_cooldown = datetime.now() + timedelta(hours=2)
        assert should_trigger_with_cooldown(after_cooldown) is True

    def test_quality_threshold_enforcement(self):
        """Test quality thresholds prevent low-quality automation"""

        def meets_quality_threshold(pattern_count, pattern_severity):
            if pattern_severity in ["high", "critical"]:
                return True
            if pattern_severity == "medium" and pattern_count >= 2:
                return True
            return False

        # High quality cases
        assert meets_quality_threshold(1, "critical") is True
        assert meets_quality_threshold(3, "high") is True
        assert meets_quality_threshold(2, "medium") is True

        # Low quality cases
        assert meets_quality_threshold(1, "low") is False
        assert meets_quality_threshold(1, "medium") is False

    def test_daily_limit_enforcement(self):
        """Test daily automation limits"""
        daily_limit = 5
        current_count = 0

        def can_trigger_automation():
            return current_count < daily_limit

        # Should allow up to daily limit
        for i in range(daily_limit):
            assert can_trigger_automation() is True
            current_count += 1

        # Should block after reaching limit
        assert can_trigger_automation() is False


class TestMockInfrastructure:
    """Test mock infrastructure for GitHub operations"""

    def test_mock_github_issue_creation(self):
        """Test mock GitHub issue creation"""
        # Mock GitHub API
        mock_issues = {}
        next_issue_id = 1

        def create_issue(title, body, labels=None):
            nonlocal next_issue_id
            issue = {
                "id": next_issue_id,
                "title": title,
                "body": body,
                "labels": labels or [],
                "state": "open",
            }
            mock_issues[next_issue_id] = issue
            next_issue_id += 1
            return issue

        # Test issue creation
        issue = create_issue("Test Issue", "Test Description", ["bug", "priority:high"])

        assert issue["title"] == "Test Issue"
        assert issue["body"] == "Test Description"
        assert "bug" in issue["labels"]
        assert issue["state"] == "open"
        assert len(mock_issues) == 1

    def test_mock_session_data_generation(self):
        """Test generation of realistic test session data"""

        def create_repeated_tool_session():
            messages = [
                {"role": "user", "content": "I need to process multiple files"},
            ]

            # Add repeated bash operations
            for i in range(8):
                messages.append(
                    {
                        "role": "assistant",
                        "content": f'<function_calls><invoke name="Bash"><parameter name="command">process_{i}.py</parameter></invoke></function_calls>',
                    }
                )

            return messages

        def create_error_session():
            return [
                {"role": "user", "content": "Getting errors with this script"},
                {"role": "user", "content": "Error: FileNotFoundError occurred"},
                {"role": "user", "content": "Another error: PermissionError"},
                {"role": "user", "content": "Failed again with ImportError"},
            ]

        # Test session generators
        repeated_session = create_repeated_tool_session()
        error_session = create_error_session()

        # Validate generated data
        bash_count = sum(1 for msg in repeated_session if "Bash" in msg.get("content", ""))
        error_count = sum(1 for msg in error_session if "error" in msg.get("content", "").lower())

        assert bash_count >= 8
        assert error_count >= 3


class TestIntegrationScenarios:
    """Test integration scenarios end-to-end"""

    def test_pattern_to_automation_flow(self):
        """Test complete flow from pattern detection to automation trigger"""
        # Step 1: Session with automation-worthy patterns
        session_data = {
            "patterns": [{"type": "user_frustration", "severity": "critical", "count": 3}],
            "metrics": {"total_messages": 50, "tool_uses": 15},
        }

        # Step 2: Check automation worthiness
        def is_automation_worthy(session):
            patterns = session["patterns"]
            return any(p["severity"] == "critical" for p in patterns)

        # Step 3: Mock automation trigger
        automation_triggered = False
        workflow_id = None

        if is_automation_worthy(session_data):
            automation_triggered = True
            workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Verify flow
        assert automation_triggered is True
        assert workflow_id is not None
        assert workflow_id.startswith("workflow_")

    def test_safety_gate_integration(self):
        """Test that safety gates integrate properly"""
        # Mock state tracking
        automation_state = {
            "last_trigger": datetime.now() - timedelta(minutes=30),  # 30 minutes ago
            "daily_count": 3,
            "daily_limit": 5,
            "cooldown_hours": 1,
        }

        def passes_safety_gates(state):
            # Check cooldown
            time_since_last = datetime.now() - state["last_trigger"]
            if time_since_last.total_seconds() < (state["cooldown_hours"] * 3600):
                return False

            # Check daily limit
            if state["daily_count"] >= state["daily_limit"]:
                return False

            return True

        # Should be blocked by cooldown (30 minutes < 1 hour)
        assert passes_safety_gates(automation_state) is False

        # Update state to pass cooldown
        automation_state["last_trigger"] = datetime.now() - timedelta(hours=2)
        assert passes_safety_gates(automation_state) is True

        # Update state to hit daily limit
        automation_state["daily_count"] = 5
        assert passes_safety_gates(automation_state) is False


def test_comprehensive_test_suite():
    """Meta-test: Validate that test suite covers key areas"""
    test_areas = [
        "pattern_detection",
        "safety_mechanisms",
        "rate_limiting",
        "quality_thresholds",
        "mock_infrastructure",
        "integration_flows",
    ]

    # This test validates that we have comprehensive coverage
    # In a real implementation, this would check actual test coverage
    covered_areas = []

    # Check if each area has corresponding test methods
    test_classes = [
        TestReflectionPatterns,
        TestSafetyMechanisms,
        TestMockInfrastructure,
        TestIntegrationScenarios,
    ]

    for test_class in test_classes:
        methods = [method for method in dir(test_class) if method.startswith("test_")]
        if methods:
            covered_areas.extend(
                [
                    area
                    for area in test_areas
                    if any(area.replace("_", "") in method.replace("_", "") for method in methods)
                ]
            )

    # Should cover most key areas
    unique_covered = list(set(covered_areas))
    coverage_ratio = len(unique_covered) / len(test_areas)

    assert coverage_ratio >= 0.3  # At least 30% coverage of key areas (demo)
    assert len(unique_covered) >= 2  # At least 2 key areas covered


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
