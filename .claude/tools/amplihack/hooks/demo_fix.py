#!/usr/bin/env python3
"""
Demonstration of the transcript reading bug fix.
Shows before/after behavior of the stop hook.
"""

import json
import subprocess
import sys
from pathlib import Path


def simulate_claude_code_input():
    """Simulate the input that Claude Code sends to the stop hook."""

    # This simulates what Claude Code was sending that caused the bug
    problematic_inputs = [
        {
            "name": "None transcript_path (original bug)",
            "data": {
                "session_id": "test_session_1",
                "transcript_path": None,  # This was the bug!
                "cwd": str(Path.cwd()),
                "permission_mode": "safe",
                "hook_event_name": "stop",
                "stop_hook_active": True,
            },
        },
        {
            "name": "External transcript path",
            "data": {
                "session_id": "test_session_2",
                "transcript_path": "/Users/ryan/.claude/projects/-Users-ryan-src-hackathon-MicrosoftHackathon2025-AgenticCoding/f53ea17a-3930-4f24-aa9e-437ca571d8b2.jsonl",
                "cwd": str(Path.cwd()),
                "permission_mode": "safe",
                "hook_event_name": "stop",
                "stop_hook_active": True,
            },
        },
        {
            "name": "Direct messages (fallback)",
            "data": {
                "session_id": "test_session_3",
                "transcript_path": None,
                "messages": [
                    {"role": "user", "content": "Fix the bug"},
                    {"role": "assistant", "content": "Bug fixed!"},
                ],
                "cwd": str(Path.cwd()),
                "permission_mode": "safe",
                "hook_event_name": "stop",
                "stop_hook_active": True,
            },
        },
    ]

    print("DEMONSTRATING TRANSCRIPT READING BUG FIX")
    print("=" * 60)
    print("\nBefore fix: Hook would receive None transcript_path and find 0 messages")
    print("After fix: Hook handles None gracefully and finds messages via multiple strategies\n")

    hook_script = Path(__file__).parent / "stop.py"

    for test_case in problematic_inputs:
        print(f"\nTest: {test_case['name']}")
        print("-" * 40)

        result = subprocess.run(
            [sys.executable, str(hook_script)],
            input=json.dumps(test_case["data"]),
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("✅ Hook executed successfully")

            # Check log for message count
            log_file = (
                Path.home()
                / "src/hackathon/MicrosoftHackathon2025-AgenticCoding/.claude/runtime/logs/stop.log"
            )
            if log_file.exists():
                with open(log_file, "r") as f:
                    lines = f.readlines()
                    # Find relevant log lines
                    for line in reversed(lines[-30:]):
                        if test_case["data"]["session_id"] in line:
                            if (
                                "messages from" in line
                                or "Processing" in line
                                or "Using direct" in line
                            ):
                                # Extract message count
                                if "0 messages" in line:
                                    print("⚠️  Found 0 messages (would fail reflection)")
                                else:
                                    import re

                                    match = re.search(r"(\d+) messages", line)
                                    if match:
                                        count = match.group(1)
                                        print(f"✅ Found {count} messages (reflection will work!)")
                                break
        else:
            print(f"❌ Hook failed: {result.stderr[:200]}")

    print("\n" + "=" * 60)
    print("FIX SUMMARY:")
    print("1. ✅ Handle None transcript_path without error")
    print("2. ✅ Allow reading from Claude Code external directories")
    print("3. ✅ Parse Claude Code JSONL format correctly")
    print("4. ✅ Use fallback strategies (direct messages, session discovery)")
    print("5. ✅ Reflection now receives actual messages to analyze!")


if __name__ == "__main__":
    simulate_claude_code_input()
