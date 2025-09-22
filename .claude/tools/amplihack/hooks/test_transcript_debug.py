#!/usr/bin/env python3
"""
Debug script to understand transcript path and format.
This simulates what the stop hook receives to help diagnose the issue.
"""

import json
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from stop import StopHook


def create_test_transcript():
    """Create a test transcript file to verify reading works"""
    project_root = Path(__file__).resolve().parents[4]
    test_dir = project_root / ".claude" / "runtime" / "test"
    test_dir.mkdir(exist_ok=True)

    test_messages = [
        {"role": "user", "content": "Hello, can you help me implement a reflection system?"},
        {
            "role": "assistant",
            "content": "I'll help you implement a reflection system. Let me analyze your current setup and suggest improvements.",
        },
        {
            "role": "user",
            "content": "The reflection hooks run but process zero messages because they can't read session transcripts.",
        },
        {
            "role": "assistant",
            "content": "I can see the issue. The stop hook is receiving transcript_path but not reading the file properly. Let me fix this.",
        },
    ]

    # Create test transcript file within project
    test_file = test_dir / "test_transcript.json"
    with open(test_file, "w") as f:
        json.dump(test_messages, f, indent=2)
    return str(test_file)


def simulate_stop_hook_input():
    """Simulate the input that Claude Code sends to stop hook"""

    # Create test transcript
    test_transcript_path = create_test_transcript()
    print(f"Created test transcript: {test_transcript_path}")

    # This is the typical input format based on logs
    mock_input = {
        "session_id": "20250921_230000",
        "transcript_path": test_transcript_path,
        "cwd": "/Users/ryan/src/hackathon/MicrosoftHackathon2025-AgenticCoding",
        "permission_mode": "normal",
        "hook_event_name": "stop",
        "stop_hook_active": True,
    }

    # Test the hook
    hook = StopHook()
    print("=== Testing Stop Hook Transcript Reading ===")
    print(f"Mock input: {json.dumps(mock_input, indent=2)}")
    print()

    # Test transcript reading with valid path
    print("Testing with valid transcript path...")
    result = hook.process(mock_input)
    print(f"Result: {json.dumps(result, indent=2)}")
    print()

    # Test with non-existent path
    print("Testing with non-existent transcript path...")
    mock_input["transcript_path"] = "/some/path/to/transcript.json"
    result = hook.process(mock_input)
    print(f"Result: {json.dumps(result, indent=2)}")
    print()

    # Test with empty transcript path
    print("Testing with empty transcript path...")
    mock_input["transcript_path"] = ""
    result = hook.process(mock_input)
    print(f"Result: {json.dumps(result, indent=2)}")
    print()

    # Test with direct messages
    print("Testing with direct messages...")
    mock_input = {
        "messages": [
            {"role": "user", "content": "This is a test with direct messages"},
            {"role": "assistant", "content": "I understand. This tests the direct message path."},
        ]
    }
    result = hook.process(mock_input)
    print(f"Result: {json.dumps(result, indent=2)}")
    print()

    # Cleanup
    import os

    os.unlink(test_transcript_path)

    # Check for actual transcript files in common locations
    print("=== Looking for actual transcript files ===")
    project_root = Path(__file__).resolve().parents[4]

    potential_paths = [
        project_root / ".claude" / "runtime" / "transcripts",
        project_root / ".claude" / "runtime" / "sessions",
        project_root / ".claude" / "runtime" / "logs",
        project_root / "transcripts",
        project_root / "sessions",
    ]

    for path in potential_paths:
        if path.exists():
            print(f"Found directory: {path}")
            files = list(path.glob("*"))[:5]  # First 5 files
            for f in files:
                print(f"  - {f.name}")
        else:
            print(f"Directory doesn't exist: {path}")


if __name__ == "__main__":
    simulate_stop_hook_input()
