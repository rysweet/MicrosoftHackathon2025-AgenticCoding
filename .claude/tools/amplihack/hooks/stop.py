#!/usr/bin/env python3
"""
Claude Code hook for stop events.
Checks lock flag and blocks stop if continuous work mode is enabled.

Stop Hook Protocol (https://docs.claude.com/en/docs/claude-code/hooks):
- Return {"decision": "approve"} to allow normal stop
- Return {"decision": "block", "reason": "..."} to prevent stop and continue working
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# Clean import structure
sys.path.insert(0, str(Path(__file__).parent))
from hook_processor import HookProcessor


class StopHook(HookProcessor):
    """Hook processor for stop events with lock support."""

    def __init__(self):
        super().__init__("stop")
        self.lock_flag = self.project_root / ".claude" / "runtime" / "locks" / ".lock_active"

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check lock flag and block stop if active.
        Run synchronous reflection analysis if enabled.

        Args:
            input_data: Input from Claude Code

        Returns:
            Dict with decision to block or allow stop
        """
        # LOG START - Always log entry for debugging
        self.log("=== STOP HOOK STARTED ===")
        self.log(f"Input keys: {list(input_data.keys())}")

        try:
            lock_exists = self.lock_flag.exists()
        except (PermissionError, OSError) as e:
            self.log(f"Cannot access lock file: {e}", "WARNING")
            self.log("=== STOP HOOK ENDED (fail-safe: approve) ===")
            # Fail-safe: allow stop if we can't read lock
            return {"decision": "approve"}

        if lock_exists:
            # Lock is active - block stop and continue working
            self.log("Lock is active - blocking stop to continue working")
            self.save_metric("lock_blocks", 1)
            self.log("=== STOP HOOK ENDED (decision: block - lock active) ===")
            return {
                "decision": "block",
                "reason": "we must keep pursuing the user's objective and must not stop the turn - look for any additional TODOs, next steps, or unfinished work and pursue it diligently in as many parallel tasks as you can",
            }

        # Check if reflection should run
        if not self._should_run_reflection():
            self.log("Reflection not enabled or skipped - allowing stop")
            self.log("=== STOP HOOK ENDED (decision: approve - no reflection) ===")
            return {"decision": "approve"}

        # RUN REFLECTION SYNCHRONOUSLY (blocks here)
        try:
            filled_template = self._run_reflection_sync()

            # If reflection failed or returned nothing, allow stop
            if not filled_template or not filled_template.strip():
                self.log("No reflection result - allowing stop")
                self.log("=== STOP HOOK ENDED (decision: approve - no reflection) ===")
                return {"decision": "approve"}

            # Emit reflection to stderr
            self._emit_reflection_output(filled_template)

            # Block stop and tell Claude to read the reflection
            self.log("Reflection complete - blocking for user review")
            result = self._block_for_reflection(filled_template)
            self.log("=== STOP HOOK ENDED (decision: block - reflection complete) ===")
            return result

        except Exception as e:
            # FAIL-SAFE: Always allow stop on errors
            self.log(f"Reflection error: {e}", "ERROR")
            self.save_metric("reflection_errors", 1)
            self.log("=== STOP HOOK ENDED (decision: approve - error occurred) ===")
            return {"decision": "approve"}

    def _should_run_reflection(self) -> bool:
        """Check if reflection should run based on config and environment.

        Returns:
            True if reflection should run, False otherwise
        """
        # Check environment variable skip flag
        if os.environ.get("AMPLIHACK_SKIP_REFLECTION"):
            self.log("AMPLIHACK_SKIP_REFLECTION is set - skipping reflection", "DEBUG")
            return False

        # Load reflection config
        config_path = (
            self.project_root / ".claude" / "tools" / "amplihack" / ".reflection_config"
        )
        if not config_path.exists():
            self.log("Reflection config not found - skipping reflection", "DEBUG")
            return False

        try:
            with open(config_path) as f:
                config = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            self.log(f"Cannot read reflection config: {e}", "WARNING")
            return False

        # Check if enabled
        if not config.get("enabled", False):
            self.log("Reflection is disabled - skipping", "DEBUG")
            return False

        # Check for reflection lock to prevent concurrent runs
        reflection_dir = self.project_root / ".claude" / "runtime" / "reflection"
        reflection_lock = reflection_dir / ".reflection_lock"

        if reflection_lock.exists():
            self.log("Reflection already running - skipping", "DEBUG")
            return False

        return True

    def _get_current_session_id(self) -> str:
        """Detect current session ID from environment or logs.

        Priority:
        1. CLAUDE_SESSION_ID env var (if set by tooling)
        2. Most recent session directory
        3. Generate timestamp-based ID

        Returns:
            Session ID string
        """
        # Try environment variable
        session_id = os.environ.get("CLAUDE_SESSION_ID")
        if session_id:
            return session_id

        # Try finding most recent session
        logs_dir = self.project_root / ".claude" / "runtime" / "logs"
        if logs_dir.exists():
            try:
                sessions = sorted(
                    logs_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True
                )
                if sessions:
                    return sessions[0].name
            except (OSError, PermissionError) as e:
                self.log(f"Cannot access logs directory: {e}", "WARNING")

        # Generate timestamp-based ID
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def _run_reflection_sync(self) -> Optional[str]:
        """Run Claude SDK-based reflection synchronously.

        Returns:
            Filled FEEDBACK_SUMMARY template as string, or None if failed
        """
        try:
            from claude_reflection import run_claude_reflection
        except ImportError:
            self.log("Cannot import claude_reflection - skipping reflection", "WARNING")
            return None

        # Get session ID
        session_id = self._get_current_session_id()
        self.log(f"Running Claude-powered reflection for session: {session_id}")

        # Find session directory
        session_dir = self.project_root / ".claude" / "runtime" / "logs" / session_id

        if not session_dir.exists():
            self.log(f"Session directory not found: {session_dir}", "WARNING")
            return None

        # Run Claude reflection (uses SDK)
        try:
            filled_template = run_claude_reflection(session_dir, self.project_root)

            if not filled_template:
                self.log("Claude reflection returned empty result", "WARNING")
                return None

            # Save the filled template
            output_path = session_dir / "FEEDBACK_SUMMARY.md"
            output_path.write_text(filled_template)
            self.log(f"Feedback summary saved to: {output_path}")

            # Also save to current_findings for backward compatibility
            findings_path = (
                self.project_root / ".claude" / "runtime" / "reflection" / "current_findings.md"
            )
            findings_path.parent.mkdir(parents=True, exist_ok=True)
            findings_path.write_text(filled_template)

            # Save metrics
            self.save_metric("reflection_success", 1)

            return filled_template

        except Exception as e:
            self.log(f"Claude reflection failed: {e}", "ERROR")
            return None

    def _emit_reflection_output(self, filled_template: str) -> None:
        """Emit reflection output to stderr for immediate visibility.

        Args:
            filled_template: Filled FEEDBACK_SUMMARY template
        """
        print(f"\n{'=' * 70}", file=sys.stderr)
        print("CLAUDE-POWERED SESSION REFLECTION COMPLETE", file=sys.stderr)
        print(f"{'=' * 70}\n", file=sys.stderr)

        # Show first 500 chars as preview
        preview = filled_template[:500]
        if len(filled_template) > 500:
            preview += "\n\n[... content truncated ...]"

        print(preview, file=sys.stderr)
        print(f"\n{'=' * 70}", file=sys.stderr)
        print("Full reflection saved to:", file=sys.stderr)
        print("  .claude/runtime/reflection/current_findings.md", file=sys.stderr)
        print(f"{'=' * 70}\n", file=sys.stderr)

    def _block_for_reflection(self, filled_template: str) -> Dict:
        """Block stop and instruct Claude to present reflection to user.

        Args:
            filled_template: Filled FEEDBACK_SUMMARY template from Claude

        Returns:
            Block decision dict with reason
        """
        session_id = self._get_current_session_id()
        findings_path = ".claude/runtime/reflection/current_findings.md"

        reason = f"""Session reflection has been completed by Claude analyzing the conversation.

**Reflection saved to:** {findings_path}

Before stopping, please:

1. Read the reflection file: {findings_path}
2. Present the key findings and recommendations to the user
3. Ask the user if they want to:
   - Create GitHub issues for any improvement opportunities
   - Save this reflection for future reference
   - Or skip and stop normally

After the user reviews the reflection, you may stop the session.

The user can also say "skip reflection" to stop immediately."""

        self.save_metric("reflection_blocked", 1)

        return {"decision": "block", "reason": reason}


def main():
    """Entry point for the stop hook."""
    hook = StopHook()
    hook.run()


if __name__ == "__main__":
    main()
