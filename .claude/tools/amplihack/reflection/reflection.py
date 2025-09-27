"""Simple AI-powered reflection system with user visibility.

Analyzes session logs and creates GitHub issues for improvements.
Shows the user what's happening during reflection analysis.
"""

import json
import os
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

from display import (
    show_analysis_complete,
    show_analysis_start,
    show_automation_status,
    show_error,
    show_issue_created,
    show_pattern_found,
)


def sanitize_messages(messages: List[Dict], max_messages: int = 20) -> List[Dict]:
    """Sanitize messages for processing with optimized string operations."""
    if not messages:
        return []

    sanitized = []
    for msg in messages[:max_messages]:
        content = msg.get("content", "")
        if not isinstance(content, str):
            content = str(content)

        # More efficient truncation
        if len(content) > 100:
            content = content[:100] + "..."

        sanitized.append({"content": content})

    return sanitized


def sanitize_content(content: str, max_length: int = 200) -> str:
    """Sanitize content with length limit."""
    return content[:max_length] + ("..." if len(content) > max_length else "")


def filter_pattern_suggestion(suggestion: str) -> str:
    """Filter suggestions for safety."""
    return suggestion[:100] + ("..." if len(suggestion) > 100 else "")


@lru_cache(maxsize=1)
def is_reflection_enabled() -> bool:
    """Check if reflection is enabled via environment variable with caching."""
    return os.environ.get("REFLECTION_ENABLED", "true").lower() not in {"false", "0", "no", "off"}


def analyze_session_patterns(messages: List[Dict]) -> List[Dict]:
    """Analyze session for improvement patterns with optimized processing."""
    if not messages:
        return []

    # Optimize sanitization with larger batch size
    safe_messages = sanitize_messages(messages, max_messages=30)

    # Build content more efficiently with size limits
    content_parts = []
    total_length = 0
    max_content_length = 8000  # Limit total content to improve performance

    for msg in safe_messages:
        content_str = msg.get("content", "")
        if total_length + len(content_str) > max_content_length:
            break
        content_parts.append(content_str)
        total_length += len(content_str)

    content = " ".join(content_parts).lower()

    patterns = []

    # Optimized pattern detection with early evaluation
    error_indicators = {"error", "failed", "exception", "traceback"}
    workflow_indicators = {"try again", "repeat", "redo"}

    # Use set intersection for efficient word matching
    content_words = set(content.split())

    if error_indicators & content_words:
        patterns.append(
            {
                "type": "error_handling",
                "priority": "high",
                "suggestion": "Improve error handling based on session failures",
            }
        )

    if any(indicator in content for indicator in workflow_indicators):
        patterns.append(
            {
                "type": "workflow",
                "priority": "medium",
                "suggestion": "Streamline workflow to reduce repetitive actions",
            }
        )

    # Optimized counting with early exit
    tool_count = content.count("tool_use")
    if tool_count > 10:
        patterns.append(
            {
                "type": "automation",
                "priority": "medium",
                "suggestion": f"Consider automating frequent tool combinations ({tool_count} uses detected)",
            }
        )

    # Process suggestions in batch
    for pattern in patterns:
        pattern["suggestion"] = filter_pattern_suggestion(pattern["suggestion"])

    return patterns


def create_github_issue(pattern: Dict) -> Optional[str]:
    """Create GitHub issue for improvement pattern."""
    try:
        safe_type = sanitize_content(pattern.get("type", "unknown"), 50)
        safe_suggestion = filter_pattern_suggestion(pattern.get("suggestion", ""))
        safe_priority = sanitize_content(pattern.get("priority", "medium"), 20)

        title = f"AI-detected {safe_type}: {safe_suggestion[:60]}"
        body = f"""# AI-Detected Improvement Opportunity

**Type**: {safe_type}
**Priority**: {safe_priority}

## Suggestion
{safe_suggestion}

## Next Steps
This improvement was identified by AI analysis. Please review and implement as appropriate.
"""

        result = subprocess.run(
            [
                "gh",
                "issue",
                "create",
                "--title",
                title,
                "--body",
                body,
                "--label",
                f"ai-improvement,{safe_type},{safe_priority}-priority",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            issue_url = result.stdout.strip()
            show_issue_created(issue_url, pattern["type"])
            return issue_url.split("/")[-1] if issue_url else None

        show_error(f"Failed to create GitHub issue: {result.stderr}")
        return None
    except Exception as e:
        show_error(f"Exception creating GitHub issue: {e}")
        return None


def delegate_to_ultrathink(issue_number: str, pattern: Dict) -> bool:
    """Delegate issue to UltraThink for automated fix."""
    try:
        task = f"Fix GitHub issue #{issue_number}: {pattern['suggestion']}"
        result = subprocess.run(
            ["claude", "ultrathink", task], capture_output=True, text=True, timeout=300
        )
        success = result.returncode == 0
        show_automation_status(issue_number, success)
        return success
    except Exception as e:
        show_error(f"Failed to delegate to UltraThink: {e}")
        return False


def process_reflection_analysis(messages: List[Dict]) -> Optional[str]:
    """Main reflection analysis entry point with user visibility."""

    if not is_reflection_enabled():
        print("ℹ️  Reflection analysis disabled (set REFLECTION_ENABLED=true to enable)")
        return None

    try:
        # Validate messages input
        if not messages:
            show_error("No session messages provided for analysis")
            return None

        # Start analysis with user visibility
        show_analysis_start(len(messages))

        # Analyze patterns
        patterns = analyze_session_patterns(messages)

        # Show discovered patterns
        for i, pattern in enumerate(patterns, 1):
            show_pattern_found(pattern["type"], pattern["suggestion"], pattern["priority"])

        # Create issue for highest priority pattern
        issue_number = None
        if patterns:
            priority_map = {"high": 3, "medium": 2, "low": 1}
            top_pattern = max(patterns, key=lambda p: priority_map[p["priority"]])
            issue_number = create_github_issue(top_pattern)
            if issue_number:
                delegate_to_ultrathink(issue_number, top_pattern)

        # Show completion
        show_analysis_complete(len(patterns), 1 if patterns else 0)

        return issue_number if patterns else None

    except Exception as e:
        show_error(f"Reflection analysis failed: {e}")
        return None


def main():
    """CLI interface for testing."""
    if len(sys.argv) != 2:
        print("Usage: python simple_reflection.py <analysis_file.json>")
        sys.exit(1)

    try:
        analysis_path = Path(sys.argv[1])
        if not analysis_path.exists():
            print(f"Error: Analysis file not found: {analysis_path}")
            sys.exit(1)

        with open(analysis_path) as f:
            data = json.load(f)

        messages = data.get("messages", [])
        if not messages and "learnings" in data:
            messages = [{"content": str(data["learnings"])}]

        if not messages:
            print("Error: No session messages found for analysis")
            sys.exit(1)

        result = process_reflection_analysis(messages)
        print(f"Issue created: #{result}" if result else "No issues created")

    except Exception as e:
        print(f"Error processing analysis file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
