#!/usr/bin/env python3
"""
Claude Code hook for session stop events.
Captures learnings, performs reflection analysis, and optionally triggers Stage 2 PR generation.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Add project to path if needed
# Go up 5 levels: hooks -> amplihack -> tools -> .claude -> project_root
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import Stage 2 reflection module
from reflection_stage2 import PatternToPRConverter, ReflectionReportGenerator  # noqa: E402

# Directories - use .claude at project root (not nested)
LOG_DIR = project_root / ".claude" / "runtime" / "logs"
ANALYSIS_DIR = project_root / ".claude" / "runtime" / "analysis"
REPORTS_DIR = project_root / ".claude" / "runtime" / "reports"
LOG_DIR.mkdir(parents=True, exist_ok=True)
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def log(message: str, level: str = "INFO"):
    """Simple logging to file"""
    timestamp = datetime.now().isoformat()
    log_file = LOG_DIR / "stop.log"

    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] {level}: {message}\n")


def extract_learnings(messages: list) -> list:
    """Extract potential learnings from conversation"""
    learnings = []

    # Look for patterns indicating discoveries
    keywords = [
        "discovered",
        "learned",
        "found that",
        "turns out",
        "issue was",
        "solution was",
        "pattern",
    ]

    for message in messages:
        content = message.get("content", "")
        if isinstance(content, str):
            for keyword in keywords:
                if keyword.lower() in content.lower():
                    # Could use more sophisticated extraction here
                    learnings.append({"keyword": keyword, "preview": content[:200]})
                    break

    return learnings


def analyze_tool_usage(messages: list) -> Dict[str, int]:
    """Analyze tool usage patterns in the session."""
    tool_counts = {}

    for msg in messages:
        if msg.get("role") == "assistant":
            content = str(msg.get("content", ""))
            # Look for tool invocations
            if "antml:function_calls" in content:
                # Simple pattern matching for tool names
                tools = [
                    "Bash",
                    "Read",
                    "Write",
                    "Edit",
                    "MultiEdit",
                    "Grep",
                    "Glob",
                    "WebFetch",
                    "TodoWrite",
                ]
                for tool in tools:
                    if f'name="{tool}"' in content:
                        tool_counts[tool] = tool_counts.get(tool, 0) + 1

    return tool_counts


def calculate_session_duration(messages: list) -> int:
    """Calculate session duration in minutes."""
    if len(messages) < 2:
        return 0

    # Estimate based on message count (rough approximation)
    # Assume average 30 seconds per message exchange
    return max(1, len(messages) // 4)


def save_session_analysis(messages: list) -> "tuple[Path, Dict[str, Any]]":
    """Save session analysis for later review and Stage 1 reflection."""
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    analysis_file = ANALYSIS_DIR / f"session_{session_id}.json"

    # Extract comprehensive stats for Stage 1
    tool_usage = analyze_tool_usage(messages)
    duration_minutes = calculate_session_duration(messages)

    stats = {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "message_count": len(messages),
        "tool_uses": sum(tool_usage.values()),
        "tool_usage": tool_usage,  # Detailed tool breakdown
        "errors": 0,
        "duration_minutes": duration_minutes,
    }

    # Count errors
    for msg in messages:
        if msg.get("role") == "assistant":
            content = msg.get("content", "")
            if "error" in str(content).lower():
                stats["errors"] += 1

    # Extract learnings
    learnings = extract_learnings(messages)
    if learnings:
        stats["potential_learnings"] = len(learnings)

    # Create Stage 1 analysis structure
    stage1_analysis = {
        "session_id": session_id,
        "timestamp": stats["timestamp"],
        "metrics": stats,
        "learnings": learnings,
        "messages_sample": messages[-5:] if len(messages) > 5 else messages,  # Last few messages
    }

    # Save analysis
    with open(analysis_file, "w") as f:
        json.dump(stage1_analysis, f, indent=2)

    log(f"Saved session analysis to {analysis_file.name}")

    return analysis_file, stage1_analysis


def trigger_stage2_reflection(
    analysis_file: Path, stage1_data: Dict[str, Any], create_prs: bool = False
) -> Optional[Dict[str, Any]]:
    """Trigger Stage 2 reflection to convert insights to PRs."""
    try:
        # Initialize Stage 2 converter
        converter = PatternToPRConverter(project_root)

        # Convert to PR proposals
        stage2_results = converter.convert_to_prs(analysis_file, create_prs=create_prs)

        # Generate comprehensive report
        reporter = ReflectionReportGenerator(project_root)
        report = reporter.generate_report(
            session_summary=stage1_data,
            stage1_analysis=converter.analyze_stage1_output(analysis_file),
            stage2_results=stage2_results,
        )

        # Save report
        report_path = reporter.save_report(report, stage1_data.get("session_id"))
        log(f"Generated reflection report: {report_path}")

        return {"stage2_results": stage2_results, "report_path": str(report_path)}

    except Exception as e:
        log(f"Stage 2 reflection failed: {e}", "ERROR")
        return None


def main():
    """Process stop event with optional Stage 2 reflection."""
    try:
        log("Session stopping")

        # Read input
        raw_input = sys.stdin.read()
        input_data = json.loads(raw_input)

        # Extract messages and options
        messages = input_data.get("messages", [])
        create_prs = input_data.get("create_prs", False)  # Whether to actually create PRs

        log(f"Processing {len(messages)} messages")

        # Initialize output
        output = {}

        # Save session analysis (Stage 1)
        if messages:
            analysis_file, stage1_data = save_session_analysis(messages)

            # Always run Stage 2 reflection for complete analysis
            log("Triggering Stage 2 reflection for session analysis")
            stage2_result = trigger_stage2_reflection(analysis_file, stage1_data, create_prs)

            if stage2_result:
                output["stage2"] = {
                    "proposals_count": len(stage2_result["stage2_results"]["proposals"]),
                    "issues_created": len(stage2_result["stage2_results"]["created_issues"]),
                    "prs_created": len(stage2_result["stage2_results"]["created_prs"]),
                    "report": stage2_result["report_path"],
                }

            # Build response with learnings
            learnings = extract_learnings(messages)
            if learnings:
                output["metadata"] = {
                    "learningsFound": len(learnings),
                    "source": "session_analysis",
                    "analysis_file": str(analysis_file),
                    "reminder": "Check .claude/runtime/analysis/ for session details",
                }

                if "stage2" in output:
                    output["metadata"]["stage2_report"] = output["stage2"]["report"]

                log(f"Found {len(learnings)} potential learnings")

        # Write output
        json.dump(output, sys.stdout)

    except Exception as e:
        log(f"Error: {e}", "ERROR")
        json.dump({}, sys.stdout)


if __name__ == "__main__":
    main()
