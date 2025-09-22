#!/usr/bin/env python3
"""
Unit tests for priority scoring system in reflection automation.
Tests user frustration scoring, security pattern priority, and threshold enforcement.
"""

import sys
from datetime import datetime
from pathlib import Path

import pytest

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from claude.tools.reflection_automation_pipeline import (
    ImprovementRequest,
    ReflectionMetrics,
    ReflectionPattern,
    ReflectionResult,
    _determine_severity,
)


class TestPriorityScoring:
    """Test priority scoring algorithms"""

    def test_user_frustration_scoring(self):
        """Test that user frustration gets highest priority scoring"""
        # High frustration pattern
        frustration_pattern = ReflectionPattern(
            type="user_frustration",
            severity="critical",  # Should be auto-assigned
            count=3,
            suggestion="Review approach and consider alternative solution",
            context={"indicators": ["doesn't work", "still failing", "broken"]},
            samples=["This doesn't work", "It's still failing", "This is broken"],
        )

        # Lower priority pattern for comparison
        tool_pattern = ReflectionPattern(
            type="repeated_tool_use",
            severity="medium",
            count=5,
            suggestion="Consider creating automation",
            context={"tool": "bash"},
            samples=["ls", "grep", "awk"],
        )

        # User frustration should always be critical severity
        assert frustration_pattern.severity == "critical"
        assert tool_pattern.severity == "medium"

        # Test severity determination function
        frustration_data = {"type": "user_frustration", "count": 2}
        assert _determine_severity(frustration_data) == "critical"

    def test_security_pattern_priority(self):
        """Test that security-related patterns get appropriate high priority"""
        security_pattern_data = {
            "type": "error_patterns",
            "count": 6,  # Above threshold for high severity
            "samples": ["Permission denied", "Authentication failed", "Access violation"],
        }

        severity = _determine_severity(security_pattern_data)
        assert severity == "high"

        # Create actual pattern
        security_pattern = ReflectionPattern(
            type="error_patterns",
            severity=severity,
            count=6,
            suggestion="Investigate root cause and add better error handling",
            context={"error_types": ["permission", "auth", "access"]},
            samples=["Permission denied", "Authentication failed", "Access violation"],
        )

        # Should require security review
        improvement_request = ImprovementRequest.from_reflection_pattern(
            security_pattern, {"session_id": "test_session"}
        )

        assert improvement_request.requires_security_review is True
        assert improvement_request.improvement_type == "error_handling"
        assert improvement_request.priority == "high"

    def test_threshold_enforcement(self):
        """Test that threshold enforcement works correctly for different patterns"""
        test_cases = [
            # (pattern_type, count, expected_severity)
            ("repeated_tool_use", 2, "low"),  # Below threshold
            ("repeated_tool_use", 5, "medium"),  # At threshold
            ("repeated_tool_use", 10, "high"),  # High threshold
            ("repeated_tool_use", 15, "high"),  # Above high threshold
            ("error_patterns", 1, "low"),  # Below threshold
            ("error_patterns", 3, "medium"),  # At threshold
            ("error_patterns", 5, "high"),  # High threshold
            ("error_patterns", 10, "high"),  # Above high threshold
            ("user_frustration", 1, "critical"),  # Always critical
            ("user_frustration", 10, "critical"),  # Always critical
            ("long_session", 1, "medium"),  # Always medium
            ("long_session", 100, "medium"),  # Always medium
        ]

        for pattern_type, count, expected_severity in test_cases:
            pattern_data = {"type": pattern_type, "count": count}
            actual_severity = _determine_severity(pattern_data)
            assert actual_severity == expected_severity, (
                f"Pattern {pattern_type} with count {count} should be {expected_severity}, got {actual_severity}"
            )

    def test_automation_worthiness_logic(self):
        """Test the logic that determines if reflection results warrant automation"""
        metrics = ReflectionMetrics(
            total_messages=50, user_messages=25, assistant_messages=25, tool_uses=15
        )

        # Test case 1: Single high severity pattern should trigger automation
        high_severity_pattern = ReflectionPattern(
            type="user_frustration",
            severity="critical",
            count=3,
            suggestion="Review approach",
            context={},
        )

        result_high = ReflectionResult(
            session_id="test_high",
            timestamp=datetime.now(),
            patterns=[high_severity_pattern],
            metrics=metrics,
            suggestions=["High priority fix needed"],
        )

        assert result_high.is_automation_worthy() is True

        # Test case 2: Multiple medium patterns should trigger automation
        medium_patterns = [
            ReflectionPattern(
                type="repeated_tool_use",
                severity="medium",
                count=5,
                suggestion="Create automation",
                context={"tool": "bash"},
            ),
            ReflectionPattern(
                type="error_patterns",
                severity="medium",
                count=4,
                suggestion="Better error handling",
                context={"error_count": 4},
            ),
        ]

        result_medium = ReflectionResult(
            session_id="test_medium",
            timestamp=datetime.now(),
            patterns=medium_patterns,
            metrics=metrics,
            suggestions=["Multiple improvements needed"],
        )

        assert result_medium.is_automation_worthy() is True

        # Test case 3: Single medium pattern should NOT trigger automation
        single_medium = ReflectionResult(
            session_id="test_single",
            timestamp=datetime.now(),
            patterns=[medium_patterns[0]],  # Just one medium pattern
            metrics=metrics,
            suggestions=["Minor improvement"],
        )

        assert single_medium.is_automation_worthy() is False

        # Test case 4: Only low severity patterns should NOT trigger automation
        low_patterns = [
            ReflectionPattern(
                type="repeated_tool_use",
                severity="low",
                count=2,
                suggestion="Minor optimization",
                context={"tool": "read"},
            )
        ]

        result_low = ReflectionResult(
            session_id="test_low",
            timestamp=datetime.now(),
            patterns=low_patterns,
            metrics=metrics,
            suggestions=["Minor optimization available"],
        )

        assert result_low.is_automation_worthy() is False

    def test_primary_issue_selection(self):
        """Test that the most severe pattern is correctly identified as primary issue"""
        patterns = [
            ReflectionPattern(
                type="repeated_tool_use",
                severity="low",
                count=3,
                suggestion="Minor optimization",
                context={"tool": "read"},
            ),
            ReflectionPattern(
                type="error_patterns",
                severity="high",
                count=7,
                suggestion="Fix error handling",
                context={"errors": "authentication"},
            ),
            ReflectionPattern(
                type="user_frustration",
                severity="critical",
                count=2,
                suggestion="Review approach",
                context={"frustration_level": "high"},
            ),
            ReflectionPattern(
                type="long_session",
                severity="medium",
                count=1,
                suggestion="Better task breakdown",
                context={"message_count": 150},
            ),
        ]

        metrics = ReflectionMetrics(
            total_messages=150, user_messages=75, assistant_messages=75, tool_uses=30
        )

        result = ReflectionResult(
            session_id="test_primary",
            timestamp=datetime.now(),
            patterns=patterns,
            metrics=metrics,
            suggestions=["Multiple issues detected"],
        )

        primary = result.get_primary_issue()
        assert primary is not None
        assert primary.severity == "critical"
        assert primary.type == "user_frustration"

    def test_complexity_estimation(self):
        """Test complexity estimation based on pattern characteristics"""
        # Simple case: low severity, low count
        simple_pattern = ReflectionPattern(
            type="repeated_tool_use",
            severity="low",
            count=3,
            suggestion="Minor automation",
            context={"tool": "bash"},
        )

        simple_request = ImprovementRequest.from_reflection_pattern(
            simple_pattern, {"session_id": "test_simple"}
        )

        assert simple_request.estimated_complexity == "simple"
        assert simple_request.max_lines_of_code == 200
        assert simple_request.max_components == 3

        # Medium case: high severity
        medium_pattern = ReflectionPattern(
            type="error_patterns",
            severity="high",
            count=6,
            suggestion="Complex error handling",
            context={"error_types": ["auth", "network", "validation"]},
        )

        medium_request = ImprovementRequest.from_reflection_pattern(
            medium_pattern, {"session_id": "test_medium"}
        )

        assert medium_request.estimated_complexity == "medium"

        # Complex case: very high count
        complex_pattern = ReflectionPattern(
            type="repeated_tool_use",
            severity="high",
            count=15,  # Very high count
            suggestion="Major automation overhaul",
            context={"tool": "bash", "commands": ["ls", "grep", "awk", "sed", "find"]},
        )

        complex_request = ImprovementRequest.from_reflection_pattern(
            complex_pattern, {"session_id": "test_complex"}
        )

        assert complex_request.estimated_complexity == "complex"

    def test_improvement_type_mapping(self):
        """Test that pattern types map correctly to improvement types"""
        type_mappings = [
            ("repeated_tool_use", "tooling"),
            ("error_patterns", "error_handling"),
            ("user_frustration", "workflow"),
            ("long_session", "pattern"),
            ("unknown_pattern", "pattern"),  # Default case
        ]

        for pattern_type, expected_improvement_type in type_mappings:
            pattern = ReflectionPattern(
                type=pattern_type,
                severity="medium",
                count=5,
                suggestion="Test improvement",
                context={},
            )

            request = ImprovementRequest.from_reflection_pattern(
                pattern, {"session_id": "test_mapping"}
            )

            assert request.improvement_type == expected_improvement_type

    def test_real_world_scoring_scenarios(self):
        """Test scoring with realistic scenarios from actual development sessions"""

        # Scenario 1: Developer stuck on debugging
        debugging_patterns = [
            ReflectionPattern(
                type="error_patterns",
                severity="high",
                count=8,
                suggestion="Better error handling needed",
                context={"error_types": ["FileNotFound", "PermissionError", "ImportError"]},
                samples=["FileNotFoundError: file.py not found", "PermissionError: access denied"],
            ),
            ReflectionPattern(
                type="user_frustration",
                severity="critical",
                count=4,
                suggestion="Review debugging approach",
                context={"frustration_indicators": ["doesn't work", "still broken", "confused"]},
                samples=["This doesn't work", "I'm confused why this is still broken"],
            ),
            ReflectionPattern(
                type="repeated_tool_use",
                severity="medium",
                count=12,
                suggestion="Create debugging script",
                context={"tool": "bash"},
                samples=["python debug.py", "cat error.log", "grep ERROR"],
            ),
        ]

        debugging_result = ReflectionResult(
            session_id="debugging_session",
            timestamp=datetime.now(),
            patterns=debugging_patterns,
            metrics=ReflectionMetrics(120, 60, 60, 25),
            suggestions=["Critical debugging issues detected"],
        )

        # Should definitely trigger automation due to user frustration
        assert debugging_result.is_automation_worthy() is True
        primary = debugging_result.get_primary_issue()
        assert primary.type == "user_frustration"

        # Scenario 2: Repetitive file processing task
        file_processing_patterns = [
            ReflectionPattern(
                type="repeated_tool_use",
                severity="high",
                count=20,  # Very repetitive
                suggestion="Create file processing automation",
                context={"tool": "read", "pattern": "processing similar files"},
                samples=["Read file1.py", "Read file2.py", "Read file3.py"],
            ),
            ReflectionPattern(
                type="long_session",
                severity="medium",
                count=1,
                suggestion="Break into smaller tasks",
                context={"message_count": 180},
                samples=[],
            ),
        ]

        file_result = ReflectionResult(
            session_id="file_processing_session",
            timestamp=datetime.now(),
            patterns=file_processing_patterns,
            metrics=ReflectionMetrics(180, 90, 90, 35),
            suggestions=["Automation opportunity for file processing"],
        )

        # Should trigger due to high severity repeated tool use
        assert file_result.is_automation_worthy() is True
        primary = file_result.get_primary_issue()
        assert primary.type == "repeated_tool_use"
        assert primary.severity == "high"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
