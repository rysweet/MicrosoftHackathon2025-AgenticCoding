#!/usr/bin/env python3
"""
Claude Code hook for session stop events.
Uses unified HookProcessor for common functionality.
Enhanced with reflection visibility system for user feedback.
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
        """Extract learnings using the reflection module.

        Args:
            messages: List of conversation messages

        Returns:
            List of potential learnings with improvement suggestions
        """
        try:
            # Import reflection module
            from reflection import SessionReflector, save_reflection_summary

            # Create reflector and analyze session
            reflector = SessionReflector()
            analysis = reflector.analyze_session(messages)

            # Save detailed analysis if not skipped
            if not analysis.get("skipped"):
                summary_file = save_reflection_summary(analysis, self.analysis_dir)
                if summary_file:
                    self.log(f"Reflection analysis saved to {summary_file}")

                # Return patterns found as learnings
                learnings = []
                for pattern in analysis.get("patterns", []):
                    learnings.append(
                        {
                            "type": pattern["type"],
                            "suggestion": pattern.get("suggestion", ""),
                            "priority": "high"
                            if pattern["type"] == "user_frustration"
                            else "normal",
                        }
                    )
                return learnings
            else:
                self.log("Reflection skipped (loop prevention active)")
                return []

        except ImportError as e:
            self.log(f"Could not import reflection module: {e}", "WARNING")
            # Fall back to simple keyword extraction
            return self.extract_learnings_simple(messages)
        except Exception as e:
            self.log(f"Error in reflection analysis: {e}", "ERROR")
            return []

    def extract_learnings_simple(self, messages: List[Dict]) -> List[Dict]:
        """Simple fallback learning extraction with optimized string operations."""
        keywords = {"discovered", "learned", "found that", "issue was", "solution was"}
        learnings = []

        # Process only first 50 messages for performance
        for message in messages[:50]:
            content = str(message.get("content", ""))
            content_lower = content.lower()

            # Use any() for early exit optimization
            for keyword in keywords:
                if keyword in content_lower:
                    learnings.append({"keyword": keyword, "preview": content[:200]})
                    break

        return learnings

    def save_session_analysis(self, messages: List[Dict]):
        """Save session analysis for later review."""
        analysis_file = (
            self.analysis_dir / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        # Optimize stats calculation with single pass through messages
        message_count = len(messages)
        tool_uses = 0
        errors = 0

        # Single pass optimization - avoid multiple iterations
        for msg in messages:
            if msg.get("role") == "assistant":
                content_str = str(msg.get("content", ""))
                if "tool_use" in content_str:
                    tool_uses += 1
                if "error" in content_str.lower():
                    errors += 1

        stats = {
            "timestamp": datetime.now().isoformat(),
            "message_count": message_count,
            "tool_uses": tool_uses,
            "errors": errors,
        }

        learnings = self.extract_learnings(messages)
        if learnings:
            stats["potential_learnings"] = len(learnings)

        analysis = {"stats": stats, "learnings": learnings}

        with open(analysis_file, "w") as f:
            json.dump(analysis, f, indent=2)

        self.log(f"Saved session analysis to {analysis_file.name}")

        # Save metrics
        for key, value in stats.items():
            if key != "timestamp":
                self.save_metric(key, value)

    def get_session_messages(self, input_data: Dict[str, Any]) -> List[Dict]:
        """Get session messages from direct input."""
        messages = input_data.get("messages", [])
        if messages:
            self.log(f"Using direct messages: {len(messages)} messages")
            return messages

        self.log("No session messages found in input", "WARNING")
        return []

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process stop event."""
        self.log(f"Input data keys: {list(input_data.keys())}")

        messages = self.get_session_messages(input_data)
        self.log(f"Processing {len(messages)} messages")

        # Save session analysis
        if messages:
            self.save_session_analysis(messages)

            # Try AI-powered automation (respects REFLECTION_ENABLED environment variable)
            try:
                sys.path.append(str(Path(__file__).parent.parent / "reflection"))
                from reflection import process_reflection_analysis  # type: ignore

                self.log("Starting AI-powered reflection analysis...")

                # Find the most recent analysis file
                analysis_files = list(self.analysis_dir.glob("session_*.json"))
                if analysis_files:
                    latest_analysis = max(analysis_files, key=lambda f: f.stat().st_mtime)
                    self.log(f"Processing analysis file: {latest_analysis}")

                    # Add messages to the analysis data for AI processing
                    try:
                        with open(latest_analysis, "r") as f:
                            analysis_data = json.load(f)

                        # Sanitize messages before adding to analysis - optimized
                        safe_messages = []
                        for msg in messages[:10]:  # Limit to 10 for performance
                            if isinstance(msg, dict) and "content" in msg:
                                content = str(msg["content"])
                                # Efficient truncation
                                if len(content) > 200:
                                    content = content[:200] + "..."
                                safe_messages.append(
                                    {"content": content, "role": msg.get("role", "unknown")}
                                )
                        analysis_data["messages"] = safe_messages

                        # Save updated analysis with messages
                        with open(latest_analysis, "w") as f:
                            json.dump(analysis_data, f, indent=2)

                    except Exception as e:
                        self.log(f"Warning: Could not add messages to analysis: {e}", "WARNING")

                    # Run AI analysis with console visibility
                    result = process_reflection_analysis(messages)
                    if result:
                        self.log(f"✅ AI automation completed: Issue #{result}")
                    else:
                        self.log("AI analysis complete - no automation triggered")
                else:
                    self.log("No analysis files found for AI processing", "WARNING")

            except Exception as auto_error:
                self.log(f"AI automation error: {auto_error}", "ERROR")
                import traceback

                self.log(f"Stack trace: {traceback.format_exc()}", "DEBUG")

            # Check for learnings
            learnings = self.extract_learnings(messages)

            if learnings:
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

                if priority_learnings:
                    output["metadata"]["urgentSuggestion"] = priority_learnings[0].get(
                        "suggestion", ""
                    )

                self.log(
                    f"Found {len(learnings)} potential improvements ({len(priority_learnings)} high priority)"
                )
                return output

            return {}
        # No messages found
        self.log("No session messages to analyze")
        return {}


def main():
    """Entry point for the stop hook."""
    hook = StopHook()
    hook.run()


if __name__ == "__main__":
    main()
