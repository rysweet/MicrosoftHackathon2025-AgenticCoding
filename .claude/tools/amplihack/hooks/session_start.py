#!/usr/bin/env python3
"""
Claude Code hook for session start.
Uses unified HookProcessor for common functionality.
"""

# Import the base processor
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).parent))
from hook_processor import HookProcessor


class SessionStartHook(HookProcessor):
    """Hook processor for session start events."""

    def __init__(self):
        super().__init__("session_start")

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process session start event.

        Args:
            input_data: Input from Claude Code

        Returns:
            Additional context to add to the session
        """
        # Extract prompt
        prompt = input_data.get("prompt", "")
        self.log(f"Prompt length: {len(prompt)}")

        # Save metric
        self.save_metric("prompt_length", len(prompt))

        # Build context if needed
        context_parts = []
        preferences_summary = []

        # Add project context
        context_parts.append("## Project Context")
        context_parts.append("This is the Microsoft Hackathon 2025 Agentic Coding project.")
        context_parts.append("Focus on building AI-powered development tools.")

        # Check for recent discoveries
        discoveries_file = self.project_root / "DISCOVERIES.md"
        if discoveries_file.exists():
            context_parts.append("\n## Recent Learnings")
            context_parts.append("Check DISCOVERIES.md for recent insights.")

        # Enhanced preference reading and summarization
        preferences_file = self.project_root / ".claude" / "context" / "USER_PREFERENCES.md"
        if preferences_file.exists():
            try:
                with open(preferences_file, "r") as f:
                    prefs_content = f.read()

                import re

                # Build comprehensive preference summary
                context_parts.append("\n## 🎯 Active User Preferences")

                # Extract all core preferences
                preference_patterns = {
                    "Verbosity": r"### Verbosity\s*\n\s*([^\n]+)",
                    "Communication Style": r"### Communication Style\s*\n\s*([^\n]+)",
                    "Update Frequency": r"### Update Frequency\s*\n\s*([^\n]+)",
                    "Priority Type": r"### Priority Type\s*\n\s*([^\n]+)",
                    "Collaboration Style": r"### Collaboration Style\s*\n\s*([^\n]+)",
                    "Preferred Languages": r"### Preferred Languages\s*\n\s*([^\n]+)",
                    "Coding Standards": r"### Coding Standards\s*\n\s*([^\n]+)",
                    "Workflow Preferences": r"### Workflow Preferences\s*\n\s*([^\n]+)",
                }

                active_prefs = []
                for pref_name, pattern in preference_patterns.items():
                    match = re.search(pattern, prefs_content)
                    if match:
                        value = match.group(1).strip()
                        if value and value != "(not set)":
                            # Special handling for communication style
                            if pref_name == "Communication Style" and "pirate" in value.lower():
                                active_prefs.append(f"• **{pref_name}**: {value} 🏴‍☠️")
                                preferences_summary.append(
                                    "🏴‍☠️ Pirate mode active - All responses will use pirate language"
                                )
                            else:
                                active_prefs.append(f"• **{pref_name}**: {value}")
                            self.log(f"Found preference - {pref_name}: {value}")

                if active_prefs:
                    context_parts.extend(active_prefs)

                    # Add explanation for special preferences
                    if any("pirate" in pref.lower() for pref in active_prefs):
                        context_parts.append(
                            "\n*Note: Pirate communication style is active. All agents and responses will use nautical terminology and pirate dialect.*"
                        )
                else:
                    context_parts.append(
                        "• Using default settings (no custom preferences configured)"
                    )

                # Check for learned patterns
                learned_match = re.search(r"### \[.*?\]\s*\n\s*([^\n]+)", prefs_content)
                if learned_match:
                    context_parts.append("\n## 📚 Learned Patterns")
                    context_parts.append(f"• {learned_match.group(1).strip()}")

            except Exception as e:
                self.log(f"Could not read preferences: {e}")
                # Fail silently - don't break session start

        # Add workflow information at startup
        context_parts.append("\n## 📝 Default Workflow")
        context_parts.append("The 13-step workflow is automatically followed by `/ultrathink`")
        context_parts.append("• To view the workflow: Read `.claude/workflow/DEFAULT_WORKFLOW.md`")
        context_parts.append("• To customize: Edit the workflow file directly")
        context_parts.append(
            "• Steps include: Requirements → Issue → Branch → Design → Implement → Review → Merge"
        )

        # Add verbosity instructions
        context_parts.append("\n## 🎤 Verbosity Mode")
        context_parts.append("• Current setting: balanced")
        context_parts.append(
            "• To enable verbose: Use TodoWrite tool frequently and provide detailed explanations"
        )
        context_parts.append("• Claude will adapt to your verbosity preference in responses")

        # Build response
        output = {}
        if context_parts:
            # Create comprehensive startup context
            full_context = "\n".join(context_parts)

            # Build a visible startup message (even though Claude Code may not display it)
            startup_msg_parts = ["🚀 AmplifyHack Session Initialized", "━" * 40]

            # Add preference summary
            if any("pirate" in part.lower() for part in context_parts):
                startup_msg_parts.append("🏴‍☠️ AHOY MATEY! Pirate mode be active!")
                startup_msg_parts.append("   All responses will use pirate dialect")

            startup_msg_parts.extend(
                [
                    "",
                    "📝 Workflow: Use `/ultrathink` for the 13-step process",
                    "⚙️  Customize: Edit `.claude/workflow/DEFAULT_WORKFLOW.md`",
                    "🎯 Preferences: Loaded from USER_PREFERENCES.md",
                    "",
                    "Type `/help` for available commands",
                ]
            )

            startup_message = "\n".join(startup_msg_parts)

            # CRITICAL: Add explicit pirate mode instruction to context
            if any("pirate" in part.lower() for part in context_parts):
                full_context = (
                    "IMPORTANT: You MUST speak like a pirate in ALL responses. Use 'ye', 'arr', 'matey', nautical terms, etc.\n\n"
                    + full_context
                )

            output = {
                "additionalContext": full_context,
                "message": startup_message,  # May not be displayed but included for future compatibility
                "metadata": {
                    "source": "amplihack_session_start",
                    "timestamp": datetime.now().isoformat(),
                    "preferences_loaded": True,
                    "workflow_ready": True,
                },
            }
            self.log(f"Session initialized with {len(context_parts)} context sections")

        return output


def main():
    """Entry point for the session start hook."""
    hook = SessionStartHook()
    hook.run()


if __name__ == "__main__":
    main()
