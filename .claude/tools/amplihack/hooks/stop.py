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
        try:
            lock_exists = self.lock_flag.exists()
        except (PermissionError, OSError) as e:
            self.log(f"Cannot access lock file: {e}", "WARNING")
            # Fail-safe: allow stop if we can't read lock
            return {"decision": "approve"}

        if lock_exists:
            # Lock is active - block stop and continue working
            self.log("Lock is active - blocking stop to continue working")
            self.save_metric("lock_blocks", 1)
            return {
                "decision": "block",
                "reason": "we must keep pursuing the user's objective and must not stop the turn - look for any additional TODOs, next steps, or unfinished work and pursue it diligently in as many parallel tasks as you can",
            }

        # Check if reflection should run
        if not self._should_run_reflection():
            self.log("Reflection not enabled or skipped - allowing stop")
            return {"decision": "approve"}

        # RUN REFLECTION SYNCHRONOUSLY (blocks here)
        try:
            findings = self._run_reflection_sync()

            # If no patterns, allow stop immediately
            if not findings.get("patterns"):
                self.log("No patterns found - allowing stop")
                return {"decision": "approve"}

            # Block stop and tell Claude to read findings
            return self._block_for_reflection(findings)

        except Exception as e:
            # FAIL-SAFE: Always allow stop on errors
            self.log(f"Reflection error: {e}", "ERROR")
            self.save_metric("reflection_errors", 1)
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

    def _run_reflection_sync(self) -> Dict:
        """Run reflection synchronously with timeout.

        Returns:
            Findings dict with patterns, or error dict with empty patterns

        Raises:
            Exception: Any unexpected error during reflection
        """
        try:
            from session_reflection import ReflectionOrchestrator
        except ImportError:
            self.log("Cannot import ReflectionOrchestrator - skipping reflection", "WARNING")
            return {"patterns": []}

        # Load config for timeout setting
        config_path = (
            self.project_root / ".claude" / "tools" / "amplihack" / ".reflection_config"
        )
        try:
            with open(config_path) as f:
                config = json.load(f)
        except Exception:
            config = {}

        # Create orchestrator
        orchestrator = ReflectionOrchestrator(self.project_root)

        # Get session ID
        session_id = self._get_current_session_id()
        self.log(f"Running reflection for session: {session_id}")

        # Run analysis (with basic timeout protection)
        try:
            findings = orchestrator.analyze_session(session_id)
        except Exception as e:
            self.log(f"Reflection analysis failed: {e}", "WARNING")
            return {"patterns": []}

        # Write findings file
        findings_path = (
            self.project_root / ".claude" / "runtime" / "reflection" / "current_findings.md"
        )
        self._write_findings_file(findings, findings_path)

        # Emit to stderr
        self._emit_reflection_summary(findings)

        # Save metrics
        self.save_metric("reflection_success", 1)
        self.save_metric("patterns_detected", len(findings.get("patterns", [])))

        return findings

    def _write_findings_file(self, findings: Dict, output_path: Path) -> None:
        """Write findings to markdown file.

        Args:
            findings: Analysis results dict
            output_path: Where to write the file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        content = ["# Session Reflection Findings\n"]
        content.append(f"**Generated:** {datetime.now().isoformat()}\n")

        # Patterns
        patterns = findings.get("patterns", [])
        content.append(f"\n## Patterns Detected: {len(patterns)}\n")

        for i, pattern in enumerate(patterns, 1):
            content.append(f"\n### {i}. {pattern['type'].upper()}\n")
            content.append(f"\n**Suggestion:** {pattern.get('suggestion', 'N/A')}\n")

            # Add pattern-specific details
            for key, value in pattern.items():
                if key not in ['type', 'suggestion']:
                    content.append(f"- **{key}:** {value}\n")

        # Suggestions
        suggestions = findings.get("suggestions", [])
        if suggestions:
            content.append("\n## Recommended Actions\n")
            for i, suggestion in enumerate(suggestions, 1):
                content.append(f"{i}. {suggestion}\n")

        output_path.write_text("".join(content))
        self.log(f"Findings written to: {output_path}")

    def _emit_reflection_summary(self, findings: Dict) -> None:
        """Emit concise summary to stderr for visibility.

        Args:
            findings: Analysis results dict
        """
        pattern_count = len(findings.get("patterns", []))

        print(f"\n{'=' * 60}", file=sys.stderr)
        print("REFLECTION ANALYSIS COMPLETE", file=sys.stderr)
        print(f"{'=' * 60}", file=sys.stderr)
        print(f"Patterns detected: {pattern_count}", file=sys.stderr)

        for i, pattern in enumerate(findings.get("patterns", [])[:3], 1):
            suggestion = pattern.get("suggestion", "N/A")
            if len(suggestion) > 60:
                suggestion = suggestion[:57] + "..."
            print(f"{i}. {pattern['type']}: {suggestion}", file=sys.stderr)

        print(
            f"\nFull findings: .claude/runtime/reflection/current_findings.md",
            file=sys.stderr,
        )
        print(f"{'=' * 60}\n", file=sys.stderr)

    def _block_for_reflection(self, findings: Dict) -> Dict:
        """Block stop and instruct Claude to read findings.

        Args:
            findings: Analysis results dict

        Returns:
            Block decision dict with reason
        """
        session_id = self._get_current_session_id()
        findings_path = ".claude/runtime/reflection/current_findings.md"

        reason = f"""Session reflection analysis has completed. Before stopping, please:

1. Read the findings file: {findings_path}
2. Review the patterns detected and suggested actions
3. Ask the user if they want to create GitHub issues for any patterns
4. If user approves, use the gh CLI to create issues for each approved pattern
5. Save feedback summary to .claude/runtime/logs/{session_id}/FEEDBACK_SUMMARY.md using the template

After completing these steps, you may stop the session normally.
The user can also skip this step by saying "skip reflection"."""

        self.save_metric("reflection_blocked", 1)
        self.save_metric("patterns_detected", len(findings.get("patterns", [])))

        return {"decision": "block", "reason": reason}


def main():
    """Entry point for the stop hook."""
    hook = StopHook()
    hook.run()


if __name__ == "__main__":
    main()
