#!/usr/bin/env python3
"""
Claude Code hook for session stop events.
Uses unified HookProcessor for common functionality.
"""

import json

# Import the base processor
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).parent))
from hook_processor import HookProcessor


class StopHook(HookProcessor):
    """Hook processor for session stop events."""

    def __init__(self):
        super().__init__("stop")

    def extract_learnings(self, messages: List[Dict]) -> List[Dict]:
        """Extract potential learnings from conversation.

        Args:
            messages: List of conversation messages

        Returns:
            List of potential learnings
        """
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

    def save_session_analysis(self, messages: List[Dict]):
        """Save session analysis for later review.

        Args:
            messages: List of conversation messages
        """
        # Generate analysis filename
        analysis_file = (
            self.analysis_dir / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

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
        learnings = self.extract_learnings(messages)
        if learnings:
            stats["potential_learnings"] = len(learnings)

        # Save analysis
        analysis = {"stats": stats, "learnings": learnings}

        with open(analysis_file, "w") as f:
            json.dump(analysis, f, indent=2)

        self.log(f"Saved session analysis to {analysis_file.name}")

        # Also save metrics
        self.save_metric("message_count", stats["message_count"])
        self.save_metric("tool_uses", stats["tool_uses"])
        self.save_metric("errors", stats["errors"])
        if learnings:
            self.save_metric("potential_learnings", len(learnings))

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process stop event.

        Args:
            input_data: Input from Claude Code

        Returns:
            Metadata about the session
        """
        # Extract messages
        messages = input_data.get("messages", [])
        self.log(f"Processing {len(messages)} messages")

        # Save session analysis
        if messages:
            self.save_session_analysis(messages)

        # Check for learnings
        learnings = self.extract_learnings(messages)

        # Build response
        output = {}
        if learnings:
            output = {
                "metadata": {
                    "learningsFound": len(learnings),
                    "source": "session_analysis",
                    "reminder": "Check .claude/runtime/analysis/ for session details",
                }
            }
            self.log(f"Found {len(learnings)} potential learnings")

        return output


def main():
    """Entry point for the stop hook."""
    hook = StopHook()
    hook.run()


if __name__ == "__main__":
    main()
