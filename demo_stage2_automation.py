#!/usr/bin/env python3
"""
Stage 2 Automation Engine Demonstration

This script demonstrates the intelligent decision-making capabilities
of the Stage 2 automation engine across different scenarios.
"""

import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# Add automation modules to path
project_root = Path(__file__).parent
automation_path = project_root / ".claude/tools/amplihack/automation"
sys.path.insert(0, str(automation_path))

try:
    from automation_guard import AutomationGuard
    from priority_scorer import PriorityScorer
    from stage2_engine import AutomationResult, Stage2AutomationEngine
except ImportError as e:
    print(f"❌ Could not import automation modules: {e}")
    print("Please ensure the Stage 2 automation engine is properly installed.")
    sys.exit(1)


def create_demo_analysis(scenario_name, patterns):
    """Create a demonstration reflection analysis file"""
    analysis = {
        "session_id": f"demo_{scenario_name}_{datetime.now().strftime('%H%M%S')}",
        "timestamp": datetime.now().isoformat(),
        "patterns": patterns,
        "metrics": {
            "total_messages": 75,
            "user_messages": 38,
            "assistant_messages": 37,
            "tool_uses": 18,
        },
        "suggestions": [f"Scenario: {scenario_name}"],
    }
    return analysis


def demonstrate_priority_scoring():
    """Demonstrate the priority scoring system"""
    print("🎯 PRIORITY SCORING DEMONSTRATION")
    print("=" * 50)

    scorer = PriorityScorer()

    # Different pattern scenarios
    test_patterns = [
        {
            "name": "🔴 Critical Security Issue",
            "pattern": {
                "type": "security_vulnerability",
                "severity": "critical",
                "count": 2,
                "suggestion": "Immediate security patch required",
                "context": {"scope": "system_wide", "blocking": True},
                "confidence": 0.95,
            },
        },
        {
            "name": "😤 User Frustration",
            "pattern": {
                "type": "user_frustration",
                "severity": "high",
                "count": 4,
                "suggestion": "Review approach to reduce user pain",
                "context": {"scope": "module"},
                "confidence": 0.90,
            },
        },
        {
            "name": "🔄 High-Frequency Tool Use",
            "pattern": {
                "type": "repeated_tool_use",
                "severity": "medium",
                "count": 15,
                "suggestion": "Create automation script",
                "context": {"tool": "bash", "scope": "component"},
                "confidence": 0.85,
            },
        },
        {
            "name": "⚡ Performance Issue",
            "pattern": {
                "type": "performance_bottleneck",
                "severity": "high",
                "count": 3,
                "suggestion": "Optimize slow operations",
                "context": {"critical_path": True},
                "confidence": 0.80,
            },
        },
        {
            "name": "📝 Documentation Gap",
            "pattern": {
                "type": "documentation_gap",
                "severity": "low",
                "count": 2,
                "suggestion": "Add missing documentation",
                "context": {"scope": "component"},
                "confidence": 0.70,
            },
        },
    ]

    scored_results = []
    for item in test_patterns:
        result = scorer.score_pattern(item["pattern"])
        scored_results.append((item["name"], result))

    # Sort by score (highest first)
    scored_results.sort(key=lambda x: x[1].score, reverse=True)

    print("\n📊 PRIORITY RANKINGS:")
    for i, (name, result) in enumerate(scored_results, 1):
        priority_emoji = (
            "🚨"
            if result.category == "critical_priority"
            else "⚠️"
            if result.category == "high_priority"
            else "📝"
            if result.category == "medium_priority"
            else "💭"
            if result.category == "low_priority"
            else "❌"
        )

        print(f"\n{i}. {name}")
        print(
            f"   Score: {result.score} | Category: {result.category.replace('_', ' ').title()} {priority_emoji}"
        )
        print(f"   Reasoning: {result.reasoning}")


def demonstrate_automation_guards():
    """Demonstrate automation guard safety mechanisms"""
    print("\n\n🛡️ AUTOMATION GUARDS DEMONSTRATION")
    print("=" * 50)

    # Create temporary guard for demo
    temp_dir = tempfile.mkdtemp()
    config_path = Path(temp_dir) / "demo_guard_config.json"
    state_path = Path(temp_dir) / "demo_guard_state.json"

    guard = AutomationGuard(config_path=config_path, state_path=state_path)

    # Demo scenarios
    guard_scenarios = [
        {
            "name": "🔥 Critical Security (Should Allow)",
            "score": 180,
            "pattern_type": "security_vulnerability",
            "context": {},
        },
        {
            "name": "🚫 Blacklisted Pattern (Should Block)",
            "score": 150,
            "pattern_type": "database_migration",
            "context": {},
        },
        {
            "name": "📉 Low Score (Should Block)",
            "score": 25,
            "pattern_type": "minor_optimization",
            "context": {},
        },
        {
            "name": "🏢 CI Environment (Should Block)",
            "score": 120,
            "pattern_type": "workflow_improvement",
            "context": {"ci_environment": True},
        },
        {
            "name": "👍 High Score Normal Pattern (Should Allow)",
            "score": 95,
            "pattern_type": "repeated_tool_use",
            "context": {"user_approved": True},
        },
    ]

    print("\n🔍 GUARD DECISIONS:")
    for scenario in guard_scenarios:
        should_automate, reason = guard.should_automate(
            scenario["score"], scenario["pattern_type"], scenario["context"]
        )

        decision_emoji = "✅" if should_automate else "❌"
        print(f"\n{scenario['name']}")
        print(f"   Decision: {decision_emoji} {'ALLOW' if should_automate else 'BLOCK'}")
        print(f"   Reason: {reason}")

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)


def demonstrate_engine_decisions():
    """Demonstrate end-to-end engine decision making"""
    print("\n\n🧠 ENGINE DECISION DEMONSTRATION")
    print("=" * 50)

    # Create temporary engine for demo
    temp_dir = tempfile.mkdtemp()
    config_path = Path(temp_dir) / "demo_engine_config.json"

    # Enable test mode for demo
    os.environ["AUTOMATION_TEST_MODE"] = "true"
    engine = Stage2AutomationEngine(config_path=config_path)

    demo_scenarios = [
        {
            "name": "🚨 Critical User Frustration",
            "patterns": [
                {
                    "type": "user_frustration",
                    "severity": "critical",
                    "count": 5,
                    "suggestion": "Review approach - user is blocked",
                    "context": {"scope": "system_wide", "blocking": True},
                    "confidence": 0.95,
                }
            ],
            "expected": "AUTOMATION TRIGGERED",
        },
        {
            "name": "🔄 Multiple Medium Issues",
            "patterns": [
                {
                    "type": "repeated_tool_use",
                    "severity": "medium",
                    "count": 8,
                    "suggestion": "Create automation script",
                    "context": {"tool": "bash"},
                    "confidence": 0.85,
                },
                {
                    "type": "error_patterns",
                    "severity": "medium",
                    "count": 6,
                    "suggestion": "Improve error handling",
                    "context": {"scope": "module"},
                    "confidence": 0.80,
                },
            ],
            "expected": "AUTOMATION TRIGGERED",
        },
        {
            "name": "📝 Low Priority Documentation",
            "patterns": [
                {
                    "type": "documentation_gap",
                    "severity": "low",
                    "count": 2,
                    "suggestion": "Add documentation",
                    "context": {"scope": "component"},
                    "confidence": 0.70,
                }
            ],
            "expected": "NO AUTOMATION",
        },
        {
            "name": "❓ Low Confidence Pattern",
            "patterns": [
                {
                    "type": "workflow_inefficiency",
                    "severity": "high",
                    "count": 4,
                    "suggestion": "Optimize workflow",
                    "context": {"scope": "module"},
                    "confidence": 0.45,  # Low confidence
                }
            ],
            "expected": "NO AUTOMATION (LOW CONFIDENCE)",
        },
    ]

    print("\n🤖 ENGINE DECISIONS:")
    for scenario in demo_scenarios:
        analysis_file = Path(temp_dir) / f"{scenario['name'].replace(' ', '_')}.json"
        analysis = create_demo_analysis(scenario["name"], scenario["patterns"])

        with open(analysis_file, "w") as f:
            json.dump(analysis, f, indent=2)

        # Reset guard state for each scenario
        engine.guard.state["daily_pr_count"] = 0
        engine.guard.state["failed_attempts"] = 0

        result = engine.process_reflection_insights(analysis_file)

        decision_emoji = "🚀" if result.success else "🛑"
        print(f"\n{scenario['name']}")
        print(
            f"   Decision: {decision_emoji} {'AUTOMATION TRIGGERED' if result.success else 'NO AUTOMATION'}"
        )
        print(f"   Reason: {result.message}")
        if result.score:
            print(f"   Score: {result.score}")
        if result.pattern_type:
            print(f"   Pattern Type: {result.pattern_type}")

    # Cleanup
    del os.environ["AUTOMATION_TEST_MODE"]
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)


def demonstrate_rate_limiting():
    """Demonstrate rate limiting in action"""
    print("\n\n⏱️ RATE LIMITING DEMONSTRATION")
    print("=" * 50)

    temp_dir = tempfile.mkdtemp()
    config_path = Path(temp_dir) / "rate_limit_config.json"

    # Create engine with strict limits
    engine = Stage2AutomationEngine(config_path=config_path)
    engine.guard.config["max_prs_per_day"] = 2  # Very low limit
    engine.guard.config["cooldown_hours"] = 1  # 1 hour cooldown

    # High priority pattern that would normally trigger automation
    high_priority_analysis = create_demo_analysis(
        "rate_limit_test",
        [
            {
                "type": "user_frustration",
                "severity": "critical",
                "count": 3,
                "suggestion": "Critical user issue",
                "context": {"scope": "system_wide"},
                "confidence": 0.90,
            }
        ],
    )

    analysis_file = Path(temp_dir) / "rate_limit_test.json"
    with open(analysis_file, "w") as f:
        json.dump(high_priority_analysis, f, indent=2)

    print("\n📊 RATE LIMITING SIMULATION:")
    print("(Simulating rapid successive automation attempts)")

    for attempt in range(1, 5):
        # Mock successful PR creation for first two attempts
        if attempt <= 2:
            engine.guard.record_automation_attempt(success=True, pr_number=100 + attempt)

        should_create, reason = engine.should_create_pr(high_priority_analysis["patterns"])

        status_emoji = "✅" if should_create else "❌"
        print(f"\nAttempt {attempt}: {status_emoji} {'ALLOWED' if should_create else 'BLOCKED'}")
        print(f"   Reason: {reason}")

        if attempt == 2:
            print(f"   📈 Daily limit reached ({engine.guard.config['max_prs_per_day']} PRs)")

    # Show current guard status
    status = engine.guard.get_current_status()
    print("\n📋 Final Guard Status:")
    print(f"   Daily PRs remaining: {status['daily_prs_remaining']}")
    print(f"   Failed attempts: {status['failed_attempts']}")
    print(f"   Last PR: {status['last_pr_timestamp']}")

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    """Run the complete demonstration"""
    print("🤖 STAGE 2 AUTOMATION ENGINE DEMONSTRATION")
    print("=" * 60)
    print("This demo shows the intelligent decision-making capabilities")
    print("of the Stage 2 automation engine.")
    print("=" * 60)

    try:
        demonstrate_priority_scoring()
        demonstrate_automation_guards()
        demonstrate_engine_decisions()
        demonstrate_rate_limiting()

        print("\n\n🎉 DEMONSTRATION COMPLETE")
        print("=" * 50)
        print("✅ Priority scoring: Intelligent pattern prioritization")
        print("✅ Safety guards: Comprehensive protection mechanisms")
        print("✅ Decision engine: Smart automation triggering")
        print("✅ Rate limiting: Prevents automation abuse")
        print("\nThe Stage 2 automation engine is ready for production use!")

    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
