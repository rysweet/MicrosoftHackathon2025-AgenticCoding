#!/usr/bin/env python3
"""
Test script for stop hook transcript reading functionality.
Tests various transcript formats and scenarios.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

# Test data for different transcript formats
TEST_TRANSCRIPTS = {
    "claude_code_jsonl": [
        {"type": "user", "message": {"role": "user", "content": "Test message 1"}},
        {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [{"type": "text", "text": "Test response 1"}],
            },
        },
        {"type": "user", "message": {"role": "user", "content": "Test message 2"}},
    ],
    "simple_jsonl": [
        {"role": "user", "content": "Simple message 1"},
        {"role": "assistant", "content": "Simple response 1"},
        {"role": "user", "content": "Simple message 2"},
    ],
    "wrapped_json": {
        "messages": [
            {"role": "user", "content": "Wrapped message 1"},
            {"role": "assistant", "content": "Wrapped response 1"},
        ]
    },
    "conversation_json": {
        "conversation": [
            {"role": "user", "content": "Conversation message 1"},
            {"role": "assistant", "content": "Conversation response 1"},
        ]
    },
}


def create_test_transcript(format_name, data):
    """Create a temporary transcript file with test data."""
    temp_file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".jsonl" if "jsonl" in format_name else ".json", delete=False
    )

    if "jsonl" in format_name:
        # Write JSONL format
        for item in data:
            json.dump(item, temp_file)
            temp_file.write("\n")
    else:
        # Write regular JSON
        json.dump(data, temp_file)

    temp_file.close()
    return temp_file.name


def test_stop_hook(transcript_path, session_id="test_session"):
    """Test the stop hook with a given transcript."""
    # Prepare input data for the hook
    input_data = {
        "session_id": session_id,
        "transcript_path": transcript_path,
        "cwd": str(Path.cwd()),
        "permission_mode": "safe",
        "hook_event_name": "stop",
        "stop_hook_active": True,
    }

    # Run the stop hook
    hook_script = Path(__file__).parent / "stop.py"
    result = subprocess.run(
        [sys.executable, str(hook_script)],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
    )

    print(f"\n{'=' * 60}")
    print(f"Testing transcript: {transcript_path}")
    print(f"Format: {Path(transcript_path).suffix}")

    if result.returncode == 0:
        try:
            output = json.loads(result.stdout)
            print("✓ Hook executed successfully")

            if "metadata" in output:
                metadata = output["metadata"]
                if "learningsFound" in metadata:
                    print(f"  - Learnings found: {metadata['learningsFound']}")
                if "summary" in metadata:
                    print(f"  - Summary: {metadata['summary']}")
        except json.JSONDecodeError:
            print("✗ Could not parse output JSON")
            print(f"Output: {result.stdout}")
    else:
        print(f"✗ Hook failed with return code: {result.returncode}")
        print(f"Error: {result.stderr}")

    # Check the log file for details
    log_file = (
        Path.home()
        / "src/hackathon/MicrosoftHackathon2025-AgenticCoding/.claude/runtime/logs/stop.log"
    )
    if log_file.exists():
        # Get last 20 lines of log related to this test
        with open(log_file, "r") as f:
            lines = f.readlines()
            recent_lines = [
                line
                for line in lines[-50:]
                if session_id in line or "messages from" in line or "Parsed" in line
            ]
            if recent_lines:
                print("\nRelevant log entries:")
                for line in recent_lines[-5:]:
                    print(f"  {line.strip()}")


def test_direct_messages():
    """Test with messages provided directly in input."""
    print(f"\n{'=' * 60}")
    print("Testing direct messages in input")

    input_data = {
        "session_id": "direct_test",
        "messages": [
            {"role": "user", "content": "Direct message 1"},
            {"role": "assistant", "content": "Direct response 1"},
            {"role": "user", "content": "Direct message 2"},
        ],
        "cwd": str(Path.cwd()),
        "permission_mode": "safe",
        "hook_event_name": "stop",
        "stop_hook_active": True,
    }

    hook_script = Path(__file__).parent / "stop.py"
    result = subprocess.run(
        [sys.executable, str(hook_script)],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("✓ Direct messages test passed")
    else:
        print(f"✗ Direct messages test failed: {result.stderr}")


def test_none_transcript():
    """Test with None transcript_path."""
    print(f"\n{'=' * 60}")
    print("Testing None transcript_path")

    input_data = {
        "session_id": "none_test",
        "transcript_path": None,  # This is what we're seeing in the logs
        "cwd": str(Path.cwd()),
        "permission_mode": "safe",
        "hook_event_name": "stop",
        "stop_hook_active": True,
    }

    hook_script = Path(__file__).parent / "stop.py"
    result = subprocess.run(
        [sys.executable, str(hook_script)],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("✓ None transcript test handled gracefully")
    else:
        print(f"✗ None transcript test failed: {result.stderr}")


def main():
    """Run all tests."""
    print("Testing Stop Hook Transcript Reading")
    print("=" * 60)

    # Test different transcript formats
    for format_name, data in TEST_TRANSCRIPTS.items():
        transcript_path = create_test_transcript(format_name, data)
        test_stop_hook(transcript_path, f"test_{format_name}")
        Path(transcript_path).unlink()  # Clean up

    # Test direct messages
    test_direct_messages()

    # Test None transcript_path
    test_none_transcript()

    # Test with real Claude Code transcript if available
    claude_transcript = (
        Path.home()
        / ".claude/projects/-Users-ryan-src-hackathon-MicrosoftHackathon2025-AgenticCoding/f53ea17a-3930-4f24-aa9e-437ca571d8b2.jsonl"
    )
    if claude_transcript.exists():
        print(f"\n{'=' * 60}")
        print("Testing with real Claude Code transcript")
        test_stop_hook(str(claude_transcript), "real_claude_transcript")

    print("\n" + "=" * 60)
    print("All tests completed!")


if __name__ == "__main__":
    main()
