#!/usr/bin/env python3
"""
Test script for Stage 2 Automation Engine

Verifies that the automation engine correctly processes reflection insights
and creates PRs when appropriate.
"""

import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import automation modules
sys.path.insert(0, str(Path(__file__).parent))
from automation_guard import AutomationGuard
from priority_scorer import PriorityScorer
from stage2_engine import Stage2AutomationEngine


def create_test_reflection_analysis(severity="high", pattern_type="repeated_tool_use"):
    """Create a test reflection analysis file"""
    analysis = {
        "session_id": f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "timestamp": datetime.now().isoformat(),
        "patterns": [
            {
                "type": pattern_type,
                "severity": severity,
                "count": 8,
                "suggestion": f"Automate {pattern_type.replace('_', ' ')} to improve efficiency",
                "context": {
                    "scope": "module",
                    "affected_files": ["test1.py", "test2.py"],
                    "samples": ["example1", "example2"],
                },
                "confidence": 0.9,
            }
        ],
        "metrics": {
            "total_messages": 50,
            "user_messages": 25,
            "assistant_messages": 25,
            "tool_uses": 15,
        },
        "suggestions": ["Create automation script", "Improve error handling", "Add caching layer"],
    }

    # Write to temp file
    temp_file = Path(tempfile.mktemp(suffix=".json"))
    with open(temp_file, "w") as f:
        json.dump(analysis, f, indent=2)

    return temp_file


def test_priority_scorer():
    """Test the priority scoring system"""
    print("\n=== Testing Priority Scorer ===")

    scorer = PriorityScorer()

    # Test different pattern types
    test_patterns = [
        {"type": "security_vulnerability", "severity": "critical", "count": 1},
        {"type": "user_frustration", "severity": "high", "count": 5},
        {"type": "repeated_tool_use", "severity": "medium", "count": 10},
        {"type": "documentation_gap", "severity": "low", "count": 2},
    ]

    for pattern in test_patterns:
        result = scorer.score_pattern(pattern)
        print(f"\nPattern: {pattern['type']}")
        print(f"  Score: {result.score}")
        print(f"  Category: {result.category}")
        print(f"  Reasoning: {result.reasoning}")

    # Test batch scoring
    scored = scorer.score_patterns(test_patterns)
    print(f"\nTop priority pattern: {scored[0][0]['type']} (score: {scored[0][1].score})")


def test_automation_guard():
    """Test the automation guard system"""
    print("\n=== Testing Automation Guard ===")

    guard = AutomationGuard()

    # Test various scenarios
    test_cases = [
        (150, "critical_issue", {"user_approved": True}),
        (30, "minor_issue", {}),
        (80, "blacklisted_pattern", {}),
        (100, "normal_pattern", {"ci_environment": True}),
    ]

    for score, pattern_type, context in test_cases:
        should_automate, reason = guard.should_automate(score, pattern_type, context)
        print(f"\nPattern: {pattern_type}, Score: {score}")
        print(f"  Should automate: {should_automate}")
        print(f"  Reason: {reason}")

    # Test status
    status = guard.get_current_status()
    print("\nGuard Status:")
    print(f"  Automation enabled: {status['automation_enabled']}")
    print(f"  Daily PRs remaining: {status['daily_prs_remaining']}")
    print(f"  In cooldown: {status['in_cooldown']}")


def test_stage2_engine():
    """Test the main Stage 2 automation engine"""
    print("\n=== Testing Stage 2 Automation Engine ===")

    engine = Stage2AutomationEngine()

    # Test 1: High priority pattern
    print("\n1. Testing high priority pattern:")
    test_file = create_test_reflection_analysis(severity="high", pattern_type="error_patterns")
    result = engine.process_reflection_insights(test_file)
    print(f"   Success: {result.success}")
    print(f"   Message: {result.message}")
    if result.workflow_id:
        print(f"   Workflow ID: {result.workflow_id}")
    test_file.unlink()

    # Test 2: Low priority pattern
    print("\n2. Testing low priority pattern:")
    test_file = create_test_reflection_analysis(severity="low", pattern_type="documentation_gap")
    result = engine.process_reflection_insights(test_file)
    print(f"   Success: {result.success}")
    print(f"   Message: {result.message}")
    test_file.unlink()

    # Test 3: Should create PR decision
    print("\n3. Testing PR creation decision:")
    patterns = [
        {"type": "user_frustration", "severity": "critical", "count": 3},
        {"type": "repeated_tool_use", "severity": "medium", "count": 15},
    ]
    should_create, reason = engine.should_create_pr(patterns)
    print(f"   Should create PR: {should_create}")
    print(f"   Reason: {reason}")

    # Test 4: Engine status
    print("\n4. Testing engine status:")
    status = engine.get_status()
    print(f"   Engine enabled: {status['engine_enabled']}")
    print(f"   Active workflows: {status['active_workflows']}")
    print(f"   Guard status: {status['guard_status']['automation_enabled']}")


def test_integration():
    """Test full integration from reflection to PR decision"""
    print("\n=== Testing Full Integration ===")

    # Create components
    engine = Stage2AutomationEngine()
    scorer = PriorityScorer()
    guard = AutomationGuard()

    # Simulate a complete workflow
    print("\n1. Creating reflection analysis...")
    test_file = create_test_reflection_analysis(severity="high", pattern_type="repeated_tool_use")

    print("2. Loading and parsing analysis...")
    with open(test_file) as f:
        analysis = json.load(f)

    patterns = analysis["patterns"]
    print(f"   Found {len(patterns)} patterns")

    print("\n3. Scoring patterns...")
    scored = scorer.score_patterns(patterns)
    top_pattern, top_score = scored[0]
    print(f"   Top pattern: {top_pattern['type']}")
    print(f"   Score: {top_score.score}")
    print(f"   Category: {top_score.category}")

    print("\n4. Checking automation guards...")
    should_automate, guard_reason = guard.should_automate(top_score.score, top_pattern["type"])
    print(f"   Should automate: {should_automate}")
    print(f"   Guard reason: {guard_reason}")

    print("\n5. Processing through engine...")
    result = engine.process_reflection_insights(test_file)
    print(f"   Success: {result.success}")
    print(f"   Message: {result.message}")

    # Cleanup
    test_file.unlink()

    print("\n=== Integration Test Complete ===")


def main():
    """Run all tests"""
    print("Stage 2 Automation Engine Test Suite")
    print("=" * 50)

    # Run individual component tests
    test_priority_scorer()
    test_automation_guard()
    test_stage2_engine()

    # Run integration test
    test_integration()

    print("\n" + "=" * 50)
    print("All tests complete!")
    print("\nNote: Some tests may show 'failed' results - this is expected")
    print("when testing guard conditions and low-priority patterns.")


if __name__ == "__main__":
    main()
