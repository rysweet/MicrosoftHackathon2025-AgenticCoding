#!/usr/bin/env python3
"""
Test file for the unified stop hook implementation.
Tests all major features: transcript reading bug fix, Azure continuation, automation triggers.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from stop_unified import UnifiedStopHook


def test_transcript_path_none_bug_fix():
    """Test that transcript_path: None is handled properly (bug fix)."""
    print("Testing transcript_path: None bug fix...")

    hook = UnifiedStopHook()

    # Test with transcript_path: None
    input_data = {"transcript_path": None, "session_id": "test_session", "messages": []}

    messages = hook.get_session_messages(input_data)
    assert isinstance(messages, list)
    print("✅ transcript_path: None handled correctly")

    # Test with transcript_path as string "None"
    input_data["transcript_path"] = "None"
    messages = hook.get_session_messages(input_data)
    assert isinstance(messages, list)
    print("✅ transcript_path: 'None' handled correctly")

    # Test with empty transcript_path
    input_data["transcript_path"] = ""
    messages = hook.get_session_messages(input_data)
    assert isinstance(messages, list)
    print("✅ empty transcript_path handled correctly")


def test_configuration_loading():
    """Test configuration loading from environment and file."""
    print("Testing configuration loading...")

    # Test with environment variables
    with patch.dict(
        os.environ,
        {
            "CLAUDE_HOOK_ENABLE_AUTOMATION": "false",
            "CLAUDE_HOOK_ENABLE_AZURE_CONTINUATION": "true",
            "CLAUDE_HOOK_AUTOMATION_MIN_PATTERNS": "3",
        },
    ):
        hook = UnifiedStopHook()
        assert hook.config["enable_automation"] == False
        assert hook.config["enable_azure_continuation"] == True
        assert hook.config["automation_min_patterns"] == 3
        print("✅ Environment configuration loaded correctly")


def test_azure_continuation_detection():
    """Test Azure continuation logic."""
    print("Testing Azure continuation detection...")

    hook = UnifiedStopHook()

    # Test with TODO items
    messages_with_todos = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "TodoWrite",
                    "input": {
                        "todos": [
                            {
                                "content": "Complete task",
                                "status": "pending",
                                "activeForm": "Completing task",
                            },
                            {
                                "content": "Review code",
                                "status": "completed",
                                "activeForm": "Reviewed code",
                            },
                        ]
                    },
                }
            ],
        }
    ]

    with patch.object(hook, "is_proxy_active", return_value=True):
        result = hook.should_continue_azure(messages_with_todos)
        assert result is not None
        assert result["decision"] == "continue"
        assert "azure_uncompleted_todos" in result["reason"]
        print("✅ Azure continuation detected with pending TODOs")

    # Test with continuation phrases
    messages_with_phrases = [
        {"role": "assistant", "content": "Now let me implement the next feature"}
    ]

    with patch.object(hook, "is_proxy_active", return_value=True):
        result = hook.should_continue_azure(messages_with_phrases)
        assert result is not None
        assert result["decision"] == "continue"
        print("✅ Azure continuation detected with continuation phrases")


def test_unified_processing():
    """Test the main processing method."""
    print("Testing unified processing...")

    hook = UnifiedStopHook()

    # Test with direct messages
    input_data = {
        "messages": [
            {"role": "user", "content": "Test request"},
            {"role": "assistant", "content": "Test response"},
        ],
        "session_id": "test_session",
    }

    result = hook.process(input_data)
    assert isinstance(result, dict)
    print("✅ Unified processing works with direct messages")

    # Test with empty input
    result = hook.process({})
    assert result == {}
    print("✅ Empty input handled gracefully")


def test_feature_toggles():
    """Test that features can be disabled via configuration."""
    print("Testing feature toggles...")

    # Create hook with disabled features
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        config = {
            "enable_reflection": False,
            "enable_automation": False,
            "enable_azure_continuation": False,
        }
        json.dump(config, f)
        config_file = f.name

    try:
        # Patch the config file path
        with patch.object(Path, "exists", return_value=True):
            with patch("builtins.open", MagicMock()):
                hook = UnifiedStopHook()
                # Manually set config for test
                hook.config.update(config)

                # Test that features are disabled
                learnings, analysis = hook.extract_learnings([])
                assert learnings == []
                print("✅ Reflection disabled when configured")

                result = hook.should_continue_azure([])
                assert result is None
                print("✅ Azure continuation disabled when configured")

    finally:
        os.unlink(config_file)


def test_integration_with_hook_processor():
    """Test integration with the base HookProcessor."""
    print("Testing HookProcessor integration...")

    hook = UnifiedStopHook()

    # Test logging
    hook.log("Test message", "INFO")
    assert hook.log_file.exists()
    print("✅ Logging works correctly")

    # Test metrics saving
    hook.save_metric("test_metric", 42)
    metrics_file = hook.metrics_dir / "stop_unified_metrics.jsonl"
    assert metrics_file.exists()
    print("✅ Metrics saving works correctly")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("UNIFIED STOP HOOK TESTS")
    print("=" * 60)

    tests = [
        test_transcript_path_none_bug_fix,
        test_configuration_loading,
        test_azure_continuation_detection,
        test_unified_processing,
        test_feature_toggles,
        test_integration_with_hook_processor,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
            print()
        except Exception as e:
            print(f"❌ Test failed: {e}")
            failed += 1
            print()

    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
