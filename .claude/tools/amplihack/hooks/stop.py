#!/usr/bin/env python3
"""
Claude Code hook for session stop events.
Captures learnings and updates discoveries.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add project to path if needed
# Go up 5 levels: hooks -> amplihack -> tools -> .claude -> project_root
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Directories - use .claude at project root (not nested)
LOG_DIR = project_root / ".claude" / "runtime" / "logs"
ANALYSIS_DIR = project_root / ".claude" / "runtime" / "analysis"
LOG_DIR.mkdir(parents=True, exist_ok=True)
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)


def log(message: str, level: str = "INFO"):
    """Simple logging to file"""
    timestamp = datetime.now().isoformat()
    log_file = LOG_DIR / "stop.log"

    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] {level}: {message}\n")


def extract_learnings(messages: list) -> list:
    """Extract learnings using the reflection module"""
    try:
        # Import reflection module (local import to avoid circular dependencies)
        from reflection import SessionReflector, save_reflection_summary  # noqa: E402

        # Create reflector and analyze session
        reflector = SessionReflector()
        analysis = reflector.analyze_session(messages)

        # Save detailed analysis
        if not analysis.get("skipped"):
            summary_file = save_reflection_summary(analysis, ANALYSIS_DIR)
            log(f"Reflection analysis saved to {summary_file}")

            # Return patterns found as learnings
            learnings = []
            for pattern in analysis.get("patterns", []):
                learnings.append(
                    {
                        "type": pattern["type"],
                        "suggestion": pattern.get("suggestion", ""),
                        "priority": "high" if pattern["type"] == "user_frustration" else "normal",
                    }
                )
            return learnings
        else:
            log("Reflection skipped (loop prevention active)")
            return []

    except ImportError as e:
        log(f"Could not import reflection module: {e}", "WARNING")
        # Fall back to simple keyword extraction
        return extract_learnings_simple(messages)
    except Exception as e:
        log(f"Error in reflection analysis: {e}", "ERROR")
        return []


def extract_learnings_simple(messages: list) -> list:
    """Simple fallback learning extraction"""
    learnings = []
    keywords = ["discovered", "learned", "found that", "issue was", "solution was"]

    for message in messages:
        content = message.get("content", "")
        if isinstance(content, str):
            for keyword in keywords:
                if keyword.lower() in content.lower():
                    learnings.append({"keyword": keyword, "preview": content[:200]})
                    break
    return learnings


def save_session_analysis(messages: list):
    """Save session analysis for later review"""
    analysis_file = ANALYSIS_DIR / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    # Extract stats
    stats = {
        "timestamp": datetime.now().isoformat(),
        "message_count": len(messages),
        "tool_uses": 0,
        "errors": 0,
    }

    # Count tool uses and errors
    for msg in messages:
        if msg.get("role") == "assistant":
            content = msg.get("content", "")
            if "tool_use" in str(content):
                stats["tool_uses"] += 1
            if "error" in str(content).lower():
                stats["errors"] += 1

    # Extract learnings
    learnings = extract_learnings(messages)
    if learnings:
        stats["potential_learnings"] = len(learnings)

    # Save analysis
    analysis = {"stats": stats, "learnings": learnings}

    with open(analysis_file, "w") as f:
        json.dump(analysis, f, indent=2)

    log(f"Saved session analysis to {analysis_file.name}")


def main():
    """Process stop event"""
    try:
        log("Session stopping")

        # Read input
        raw_input = sys.stdin.read()
        input_data = json.loads(raw_input)

        # Extract messages
        messages = input_data.get("messages", [])
        log(f"Processing {len(messages)} messages")

        # Save session analysis
        if messages:
            save_session_analysis(messages)

        # Check for learnings
        learnings = extract_learnings(messages)

        # Build response
        output = {}
        if learnings:
            # Create human-readable feedback
            priority_learnings = [
                learning for learning in learnings if learning.get("priority") == "high"
            ]

            output = {
                "metadata": {
                    "learningsFound": len(learnings),
                    "highPriority": len(priority_learnings),
                    "source": "reflection_analysis",
                    "analysisPath": ".claude/runtime/analysis/",
                    "summary": f"Found {len(learnings)} improvement opportunities",
                }
            }

            # Add specific suggestions to output
            if priority_learnings:
                output["metadata"]["urgentSuggestion"] = priority_learnings[0].get("suggestion", "")

            log(
                f"Found {len(learnings)} potential improvements ({len(priority_learnings)} high priority)"
            )

        # Write output
        json.dump(output, sys.stdout)

    except Exception as e:
        log(f"Error: {e}", "ERROR")
        json.dump({}, sys.stdout)


if __name__ == "__main__":
    main()
