#!/usr/bin/env python3
"""
Test script for Stage 2 Reflection System

Tests the conversion of Stage 1 insights into PR proposals and reports.
"""

import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from reflection_stage2 import PatternToPRConverter, ReflectionReportGenerator  # noqa: E402


def create_test_stage1_data():
    """Create sample Stage 1 data for testing."""
    return {
        "session_id": "test_20250121_120000",
        "timestamp": datetime.now().isoformat(),
        "metrics": {
            "message_count": 150,
            "tool_uses": 45,
            "tool_usage": {
                "Bash": 15,  # High repetition
                "Read": 12,  # High repetition
                "Edit": 8,
                "Write": 5,
                "Grep": 5,
            },
            "errors": 7,  # Significant errors
            "duration_minutes": 45,  # Long session
        },
        "learnings": [
            {
                "keyword": "issue was",
                "preview": "The issue was unclear error messages when file not found",
            },
            {
                "keyword": "discovered",
                "preview": "Discovered that the workflow is too complex for simple tasks",
            },
            {
                "keyword": "pattern",
                "preview": "Found a pattern of repeated bash commands for file operations",
            },
        ],
        "messages_sample": [
            {"role": "user", "content": "Help me refactor this code"},
            {"role": "assistant", "content": "I'll analyze and refactor your code"},
        ],
    }


def test_pattern_analysis():
    """Test pattern extraction from Stage 1 data."""
    print("Testing Pattern Analysis...")

    # Create test data
    test_data = create_test_stage1_data()

    # Save to temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(test_data, f, indent=2)
        temp_file = Path(f.name)

    # Initialize converter
    converter = PatternToPRConverter(project_root)

    # Analyze patterns
    analysis = converter.analyze_stage1_output(temp_file)

    print(f"  Session ID: {analysis['session_id']}")
    print(f"  Patterns found: {len(analysis['patterns'])}")

    for pattern in analysis["patterns"]:
        print(f"    - Type: {pattern['type']}, Priority: {pattern['priority']}")
        print(f"      Data: {pattern['data']}")

    # Cleanup
    temp_file.unlink()

    return analysis


def test_pr_generation():
    """Test PR content generation from patterns."""
    print("\nTesting PR Content Generation...")

    # Get patterns from analysis
    analysis = test_pattern_analysis()

    # Initialize converter
    converter = PatternToPRConverter(project_root)

    # Group patterns
    proposals = converter.group_related_improvements(analysis["patterns"])
    print(f"\n  Grouped into {len(proposals)} proposals")

    # Generate PR content for each proposal
    for i, proposal in enumerate(proposals):
        print(f"\n  Proposal {i + 1} ({proposal['priority']} priority):")

        title, body, labels = converter.generate_pr_content(proposal)

        print(f"    Title: {title}")
        print(f"    Labels: {', '.join(labels)}")
        print(f"    Body preview: {body[:200]}...")


def test_report_generation():
    """Test comprehensive report generation."""
    print("\nTesting Report Generation...")

    # Create test data
    test_data = create_test_stage1_data()

    # Save to temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(test_data, f, indent=2)
        temp_file = Path(f.name)

    # Initialize components
    converter = PatternToPRConverter(project_root)
    reporter = ReflectionReportGenerator(project_root)

    # Get analysis and proposals
    analysis = converter.analyze_stage1_output(temp_file)
    stage2_results = {"proposals": [], "created_issues": [], "created_prs": [], "errors": []}

    # Generate proposals
    proposals = converter.group_related_improvements(analysis["patterns"])
    for proposal in proposals:
        title, body, labels = converter.generate_pr_content(proposal)
        stage2_results["proposals"].append(
            {
                "title": title,
                "body": body,
                "labels": labels,
                "priority": proposal["priority"],
                "pattern_type": proposal["type"],
            }
        )

    # Generate report
    report = reporter.generate_report(
        session_summary=test_data, stage1_analysis=analysis, stage2_results=stage2_results
    )

    print(f"  Report length: {len(report)} characters")
    print("\n  Report sections:")

    for line in report.split("\n"):
        if line.startswith("#"):
            print(f"    {line}")

    # Save report
    report_path = reporter.save_report(report, test_data["session_id"])
    print(f"\n  Report saved to: {report_path}")

    # Cleanup
    temp_file.unlink()


def test_end_to_end():
    """Test full Stage 2 workflow."""
    print("\nTesting End-to-End Stage 2 Workflow...")

    # Create test data
    test_data = create_test_stage1_data()

    # Save to temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(test_data, f, indent=2)
        temp_file = Path(f.name)

    # Initialize converter
    converter = PatternToPRConverter(project_root)

    # Run Stage 2 conversion (without creating actual PRs)
    results = converter.convert_to_prs(temp_file, create_prs=False)

    print(f"  Proposals generated: {len(results['proposals'])}")
    print(f"  Issues created: {len(results['created_issues'])}")
    print(f"  PRs created: {len(results['created_prs'])}")
    print(f"  Errors: {len(results['errors'])}")

    if results["proposals"]:
        print("\n  Sample proposals:")
        for i, proposal in enumerate(results["proposals"][:3]):
            print(f"    {i + 1}. [{proposal['priority']}] {proposal['title']}")

    # Save results
    results_file = temp_file.parent / f"{temp_file.stem}_stage2_test.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  Results saved to: {results_file}")

    # Cleanup
    temp_file.unlink()


def main():
    """Run all tests."""
    print("=" * 60)
    print("Stage 2 Reflection System Test Suite")
    print("=" * 60)

    try:
        # Run tests
        test_pattern_analysis()
        test_pr_generation()
        test_report_generation()
        test_end_to_end()

        print("\n" + "=" * 60)
        print("All tests completed successfully!")
        print("=" * 60)

        return 0

    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
