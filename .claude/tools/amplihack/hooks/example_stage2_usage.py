#!/usr/bin/env python3
"""
Example usage of the Stage 2 Reflection System

Shows how to use the Stage 2 reflection system to analyze session patterns
and generate improvement proposals.
"""

import json
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / ".claude" / "tools" / "amplihack" / "hooks"))

from reflection_stage2 import PatternToPRConverter, ReflectionReportGenerator  # noqa: E402


def analyze_recent_session():
    """Analyze the most recent session and generate proposals."""

    # Find the most recent Stage 1 analysis file
    analysis_dir = project_root / ".claude" / "runtime" / "analysis"

    if not analysis_dir.exists():
        print("No analysis directory found. Run a session first.")
        return

    # Get most recent session file
    session_files = sorted(analysis_dir.glob("session_*.json"), reverse=True)

    if not session_files:
        print("No session analysis files found.")
        return

    latest_session = session_files[0]
    print(f"Analyzing session: {latest_session.name}")

    # Load session data
    with open(latest_session, "r") as f:
        session_data = json.load(f)

    # Display session summary
    print("\nSession Summary:")
    print(f"  Session ID: {session_data.get('session_id', 'unknown')}")
    print(f"  Messages: {session_data['metrics']['message_count']}")
    print(f"  Duration: {session_data['metrics'].get('duration_minutes', 'N/A')} minutes")
    print(f"  Errors: {session_data['metrics']['errors']}")

    # Display tool usage
    if "tool_usage" in session_data["metrics"]:
        print("\n  Tool Usage:")
        for tool, count in session_data["metrics"]["tool_usage"].items():
            print(f"    {tool}: {count}")

    # Initialize Stage 2 converter
    converter = PatternToPRConverter(project_root)

    # Analyze patterns
    print("\nAnalyzing patterns...")
    analysis = converter.analyze_stage1_output(latest_session)

    print(f"Found {len(analysis['patterns'])} patterns:")
    for pattern in analysis["patterns"]:
        print(f"  - {pattern['type']} ({pattern['priority']})")

    # Generate proposals
    print("\nGenerating improvement proposals...")
    results = converter.convert_to_prs(latest_session, create_prs=False)

    print(f"Generated {len(results['proposals'])} proposals:")
    for i, proposal in enumerate(results["proposals"], 1):
        print(f"\n  {i}. {proposal['title']}")
        print(f"     Priority: {proposal['priority']}")
        print(f"     Type: {proposal['pattern_type']}")
        print(f"     Labels: {', '.join(proposal['labels'])}")

    # Generate report
    print("\nGenerating comprehensive report...")
    reporter = ReflectionReportGenerator(project_root)

    report = reporter.generate_report(
        session_summary=session_data, stage1_analysis=analysis, stage2_results=results
    )

    # Save report
    report_path = reporter.save_report(report, session_data.get("session_id"))
    print(f"Report saved to: {report_path}")

    # Save Stage 2 results
    results_file = latest_session.parent / f"{latest_session.stem}_stage2_example.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results saved to: {results_file}")

    return results


def create_pr_from_pattern(pattern_type: str = "repeated_commands"):
    """Example of creating a PR for a specific pattern type."""

    print(f"\nCreating PR proposal for pattern: {pattern_type}")

    # Create sample pattern data
    sample_pattern = {
        "type": pattern_type,
        "priority": "high",
        "data": {
            "command_type": "Bash",
            "count": 15,
            "pattern_details": "Repetitive bash operations detected",
            "error_type": "file_not_found",
            "error_details": "Multiple file not found errors",
            "pain_point": "complex workflow",
            "symptom_details": "Users struggling with multi-step processes",
            "task_type": "refactoring",
            "session_metrics": "45 minute session with multiple retries",
        },
    }

    # Initialize converter
    converter = PatternToPRConverter(project_root)

    # Generate PR content
    title, body, labels = converter.generate_pr_content(sample_pattern)

    print("\nGenerated PR:")
    print(f"Title: {title}")
    print(f"Labels: {', '.join(labels)}")
    print("\nBody Preview:")
    print("-" * 60)
    print(body[:500] + "...")
    print("-" * 60)

    return {"title": title, "body": body, "labels": labels}


def demo_pattern_grouping():
    """Demonstrate how related patterns are grouped."""

    print("\nDemonstrating pattern grouping...")

    # Create multiple related patterns
    patterns = [
        {
            "type": "repeated_commands",
            "priority": "high",
            "data": {"command_type": "Bash", "count": 10},
        },
        {
            "type": "repeated_commands",
            "priority": "high",
            "data": {"command_type": "Read", "count": 8},
        },
        {
            "type": "error_patterns",
            "priority": "high",
            "data": {"error_type": "permission", "count": 5},
        },
        {
            "type": "repeated_commands",
            "priority": "medium",
            "data": {"command_type": "Edit", "count": 6},
        },
    ]

    # Initialize converter
    converter = PatternToPRConverter(project_root)

    # Group patterns
    grouped = converter.group_related_improvements(patterns)

    print(f"Original patterns: {len(patterns)}")
    print(f"Grouped proposals: {len(grouped)}")

    for i, proposal in enumerate(grouped, 1):
        print(f"\n  Proposal {i}:")
        print(f"    Type: {proposal['type']}")
        print(f"    Priority: {proposal['priority']}")
        if "merged_count" in proposal:
            print(f"    Merged from: {proposal['merged_count']} patterns")
        print(f"    Data: {proposal['data']}")

    return grouped


def main():
    """Run example demonstrations."""

    print("=" * 70)
    print("Stage 2 Reflection System - Usage Examples")
    print("=" * 70)

    # Choose what to demonstrate
    print("\nSelect demonstration:")
    print("1. Analyze most recent session")
    print("2. Create PR from pattern")
    print("3. Demo pattern grouping")
    print("4. Run all demos")

    try:
        choice = input("\nEnter choice (1-4): ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nExiting...")
        return 0

    if choice == "1":
        analyze_recent_session()
    elif choice == "2":
        create_pr_from_pattern()
    elif choice == "3":
        demo_pattern_grouping()
    elif choice == "4":
        # Run all demos
        try:
            analyze_recent_session()
        except Exception as e:
            print(f"Session analysis skipped: {e}")

        create_pr_from_pattern()
        demo_pattern_grouping()
    else:
        print("Invalid choice")
        return 1

    print("\n" + "=" * 70)
    print("Demo completed successfully!")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
