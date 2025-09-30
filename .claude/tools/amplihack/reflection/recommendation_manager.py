#!/usr/bin/env python3
"""
Recommendation manager for pending recommendations.
Handles saving, displaying, and tracking of reflection recommendations.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def get_pending_dir() -> Path:
    """Get the pending recommendations directory."""
    # Path is: .claude/tools/amplihack/reflection/recommendation_manager.py
    # So parent.parent.parent gets us to the project root
    project_root = Path(__file__).parent.parent.parent.parent.parent
    pending_dir = project_root / ".claude" / "runtime" / "recommendations" / "pending"
    pending_dir.mkdir(parents=True, exist_ok=True)
    return pending_dir


def get_shown_dir() -> Path:
    """Get the shown recommendations directory."""
    # Path is: .claude/tools/amplihack/reflection/recommendation_manager.py
    # So parent.parent.parent gets us to the project root
    project_root = Path(__file__).parent.parent.parent.parent.parent
    shown_dir = project_root / ".claude" / "runtime" / "recommendations" / "shown"
    shown_dir.mkdir(parents=True, exist_ok=True)
    return shown_dir


def save_pending(
    recommendations: List[Dict],
    session_id: str,
    github_url: Optional[str] = None,
    github_error: Optional[str] = None,
) -> Path:
    """Save recommendations to pending.json for display at next session start.

    Args:
        recommendations: List of recommendation dictionaries with type, suggestion, priority
        session_id: Session identifier
        github_url: Optional GitHub issue URL if created successfully
        github_error: Optional error message if GitHub creation failed

    Returns:
        Path to the saved pending.json file
    """
    pending_dir = get_pending_dir()
    pending_file = pending_dir / "pending.json"

    data = {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "recommendations": recommendations,
        "github": {
            "url": github_url,
            "error": github_error,
            "attempted": github_url is not None or github_error is not None,
        },
    }

    with open(pending_file, "w") as f:
        json.dump(data, f, indent=2)

    return pending_file


def get_pending() -> Optional[Dict[str, Any]]:
    """Get pending recommendations if they exist.

    Returns:
        Dictionary with pending recommendations or None if no pending file exists
    """
    pending_dir = get_pending_dir()
    pending_file = pending_dir / "pending.json"

    if not pending_file.exists():
        return None

    try:
        with open(pending_file, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        # Log error but don't fail - just return None
        print(f"Warning: Could not read pending recommendations: {e}")
        return None


def mark_as_shown(session_id: str) -> bool:
    """Move pending.json to shown/ directory after displaying.

    Args:
        session_id: Session identifier for filename

    Returns:
        True if successfully moved, False otherwise
    """
    pending_dir = get_pending_dir()
    shown_dir = get_shown_dir()
    pending_file = pending_dir / "pending.json"

    if not pending_file.exists():
        return False

    try:
        # Create timestamped filename in shown directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        shown_file = shown_dir / f"shown_{session_id}_{timestamp}.json"

        # Move file
        pending_file.rename(shown_file)
        return True
    except Exception as e:
        print(f"Warning: Could not move pending recommendations: {e}")
        # Try to delete pending file at least
        try:
            pending_file.unlink()
        except Exception:
            pass
        return False


def format_recommendations_display(data: Dict[str, Any]) -> str:
    """Format recommendations for console display.

    Args:
        data: Pending recommendations data

    Returns:
        Formatted string for console output
    """
    if not data:
        return ""

    lines = []
    lines.append("")
    lines.append("=" * 80)
    lines.append("🔍 REFLECTION RECOMMENDATIONS FROM PREVIOUS SESSION")
    lines.append("=" * 80)
    lines.append("")

    # Session info
    timestamp = data.get("timestamp", "unknown")
    session_id = data.get("session_id", "unknown")
    lines.append(f"Session: {session_id}")
    lines.append(f"Time: {timestamp}")
    lines.append("")

    # Recommendations
    recommendations = data.get("recommendations", [])
    if recommendations:
        lines.append(f"Found {len(recommendations)} improvement opportunities:")
        lines.append("")

        for i, rec in enumerate(recommendations, 1):
            rec_type = rec.get("type", "unknown")
            suggestion = rec.get("suggestion", "")
            priority = rec.get("priority", "normal")

            # Priority indicator
            priority_icon = {
                "high": "🔴",
                "medium": "🟡",
                "low": "🟢",
            }.get(priority, "⚪")

            lines.append(f"{i}. {priority_icon} {rec_type.upper()}")
            lines.append(f"   {suggestion}")
            lines.append("")

    # GitHub status
    github = data.get("github", {})
    if github.get("attempted"):
        lines.append("GitHub Issue Status:")
        if github.get("url"):
            lines.append(f"✅ Created: {github['url']}")
        elif github.get("error"):
            lines.append(f"⚠️  Could not create issue: {github['error']}")
        else:
            lines.append("⚠️  GitHub issue creation attempted but status unknown")
        lines.append("")

    lines.append("=" * 80)
    lines.append("")

    return "\n".join(lines)


def cleanup_old_shown(days: int = 30) -> int:
    """Clean up shown recommendations older than specified days.

    Args:
        days: Number of days to keep shown recommendations

    Returns:
        Number of files deleted
    """
    shown_dir = get_shown_dir()
    count = 0

    try:
        import time

        cutoff_time = time.time() - (days * 24 * 60 * 60)

        for file in shown_dir.glob("shown_*.json"):
            if file.stat().st_mtime < cutoff_time:
                file.unlink()
                count += 1
    except Exception as e:
        print(f"Warning: Error cleaning up old recommendations: {e}")

    return count
