#!/usr/bin/env python3
"""
Unit tests for transcript reading and message parsing in reflection system.
Tests critical path functionality for pattern detection and analysis.
"""

import json
import sys
from pathlib import Path

import pytest

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from claude.tools.amplihack.hooks.reflection import SessionReflector


class TestTranscriptReading:
    """Test transcript reading and message parsing accuracy"""

    def setup_method(self):
        """Setup test environment"""
        self.reflector = SessionReflector()

    def test_transcript_path_none_handling(self):
        """Test handling of None transcript path"""
        # Should not crash and should skip gracefully
        result = self.reflector.analyze_session([])
        assert result is not None
        assert result.get("patterns") == []
        assert result.get("metrics", {}).get("total_messages") == 0

    def test_empty_messages_handling(self):
        """Test handling of empty message list"""
        result = self.reflector.analyze_session([])

        assert result is not None
        assert result.get("patterns") == []
        assert result.get("metrics", {}).get("total_messages") == 0
        assert result.get("metrics", {}).get("tool_uses") == 0

    def test_malformed_message_handling(self):
        """Test handling of malformed messages"""
        malformed_messages = [
            {},  # Empty message
            {"role": "user"},  # Missing content
            {"content": "test"},  # Missing role
            {"role": "unknown", "content": "test"},  # Invalid role
            {"role": "user", "content": None},  # None content
        ]

        # Should not crash with malformed input
        result = self.reflector.analyze_session(malformed_messages)
        assert result is not None
        assert "metrics" in result

    def test_message_parsing_accuracy(self):
        """Test accurate parsing of well-formed messages"""
        messages = [
            {"role": "user", "content": "Hello, can you help me with testing?"},
            {
                "role": "assistant",
                "content": "I'll help you with testing. Let me run some commands.",
            },
            {
                "role": "assistant",
                "content": '<function_calls><invoke name="Bash"><parameter name="command">ls -la</parameter></invoke></function_calls>',
            },
            {"role": "user", "content": "That's not working as expected"},
            {
                "role": "assistant",
                "content": '<function_calls><invoke name="Read"><parameter name="file_path">/test/file.py</parameter></invoke></function_calls>',
            },
        ]

        result = self.reflector.analyze_session(messages)

        # Verify basic metrics
        metrics = result.get("metrics", {})
        assert metrics.get("total_messages") == 5
        assert metrics.get("user_messages") == 2
        assert metrics.get("assistant_messages") == 3
        assert metrics.get("tool_uses") == 2  # Bash and Read

    def test_tool_extraction_accuracy(self):
        """Test accurate extraction of tool usage patterns"""
        messages = [
            {"role": "assistant", "content": '<function_calls><invoke name="Bash">'},
            {"role": "assistant", "content": '<function_calls><invoke name="Read">'},
            {"role": "assistant", "content": '<function_calls><invoke name="Write">'},
            {"role": "assistant", "content": '<function_calls><invoke name="Edit">'},
            {"role": "assistant", "content": '<function_calls><invoke name="Glob">'},
            {"role": "assistant", "content": '<function_calls><invoke name="Grep">'},
            {"role": "assistant", "content": '<function_calls><invoke name="TodoWrite">'},
        ]

        tools = self.reflector._extract_tool_uses(messages)
        expected_tools = ["bash", "read", "write", "edit", "glob", "grep", "todo"]

        assert len(tools) == len(expected_tools)
        for tool in expected_tools:
            assert tool in tools

    def test_pattern_detection_with_real_data(self):
        """Test pattern detection with realistic session data"""
        # Simulate a session with repeated bash commands
        messages = []

        # Add normal conversation
        messages.extend(
            [
                {"role": "user", "content": "I need to analyze some files"},
                {"role": "assistant", "content": "I'll help you analyze the files."},
            ]
        )

        # Add repeated bash tool usage (should trigger pattern)
        for i in range(5):
            messages.append(
                {
                    "role": "assistant",
                    "content": f'<function_calls><invoke name="Bash"><parameter name="command">ls file{i}.py</parameter></invoke></function_calls>',
                }
            )

        # Add some error indicators
        messages.extend(
            [
                {"role": "user", "content": "This is still failing, why isn't it working?"},
                {"role": "assistant", "content": "Let me check the error again"},
                {"role": "user", "content": "Error: permission denied, this is broken"},
            ]
        )

        result = self.reflector.analyze_session(messages)

        # Should detect repeated tool use
        pattern_types = [p["type"] for p in result.get("patterns", [])]
        assert "repeated_tool_use" in pattern_types
        assert "error_patterns" in pattern_types
        assert "user_frustration" in pattern_types

        # Verify pattern details
        bash_pattern = next(
            p
            for p in result["patterns"]
            if p["type"] == "repeated_tool_use" and p["tool"] == "bash"
        )
        assert bash_pattern["count"] == 5

    def test_large_transcript_handling(self):
        """Test handling of large transcripts without performance issues"""
        # Create a large message list (simulating long session)
        large_messages = []

        for i in range(200):  # Large session
            large_messages.extend(
                [
                    {"role": "user", "content": f"Request {i}"},
                    {"role": "assistant", "content": f"Response {i}"},
                ]
            )

        # Should handle large input efficiently
        import time

        start_time = time.time()
        result = self.reflector.analyze_session(large_messages)
        end_time = time.time()

        # Should complete within reasonable time (less than 1 second)
        assert (end_time - start_time) < 1.0
        assert result.get("metrics", {}).get("total_messages") == 400

        # Should detect long session pattern
        pattern_types = [p["type"] for p in result.get("patterns", [])]
        assert "long_session" in pattern_types

    def test_unicode_and_special_characters(self):
        """Test handling of unicode and special characters in messages"""
        special_messages = [
            {"role": "user", "content": "Can you help with émojis 🚀 and spéciål characters?"},
            {
                "role": "assistant",
                "content": "Sure! I'll handle ñoñó UTF-8 ✨ characters properly.",
            },
            {"role": "user", "content": 'Code snippet: \n```python\nprint("Hello 世界")\n```'},
            {
                "role": "assistant",
                "content": '<function_calls><invoke name="Bash"><parameter name="command">echo "Special chars: ±×÷"</parameter></invoke></function_calls>',
            },
        ]

        # Should handle unicode without errors
        result = self.reflector.analyze_session(special_messages)
        assert result is not None
        assert result.get("metrics", {}).get("total_messages") == 4

    def test_nested_json_in_messages(self):
        """Test handling of nested JSON structures in message content"""
        json_messages = [
            {
                "role": "user",
                "content": 'Here\'s some data: {"key": "value", "nested": {"inner": true}}',
            },
            {
                "role": "assistant",
                "content": json.dumps({"response": "processing", "data": [1, 2, 3]}),
            },
        ]

        # Should parse without JSON parsing errors
        result = self.reflector.analyze_session(json_messages)
        assert result is not None
        assert result.get("metrics", {}).get("total_messages") == 2


class TestMessageValidation:
    """Test message validation and sanitization"""

    def setup_method(self):
        """Setup test environment"""
        self.reflector = SessionReflector()

    def test_message_structure_validation(self):
        """Test validation of message structure"""
        valid_message = {"role": "user", "content": "Valid message"}
        invalid_messages = [
            None,
            "string_instead_of_dict",
            123,
            [],
            {"role": "user"},  # Missing content
            {"content": "test"},  # Missing role
        ]

        # Should handle all invalid inputs gracefully
        for invalid_msg in invalid_messages:
            try:
                result = self.reflector.analyze_session([invalid_msg])
                assert result is not None  # Should not crash
            except Exception as e:
                pytest.fail(f"Should handle invalid message gracefully: {e}")

    def test_content_sanitization(self):
        """Test content sanitization for security"""
        potentially_dangerous = [
            {"role": "user", "content": "<script>alert('xss')</script>"},
            {"role": "user", "content": "'; DROP TABLE users; --"},
            {"role": "assistant", "content": "eval(malicious_code)"},
        ]

        # Should process without executing any dangerous content
        result = self.reflector.analyze_session(potentially_dangerous)
        assert result is not None
        assert result.get("metrics", {}).get("total_messages") == 3


class TestErrorHandling:
    """Test error handling and recovery mechanisms"""

    def test_corrupted_message_recovery(self):
        """Test recovery from corrupted message data"""
        mixed_messages = [
            {"role": "user", "content": "Normal message"},
            {"role": "assistant", "content": None},  # Corrupted content
            {"role": "user", "content": "Another normal message"},
        ]

        result = self.reflector.analyze_session(mixed_messages)

        # Should recover and process valid messages
        assert result is not None
        metrics = result.get("metrics", {})
        assert metrics.get("total_messages") == 3  # Should count all messages
        assert metrics.get("user_messages") == 2  # Should count valid user messages

    def test_memory_efficient_processing(self):
        """Test memory efficiency with large datasets"""
        # Create large content to test memory handling
        large_content = "x" * 10000  # 10KB content

        memory_test_messages = [
            {"role": "user", "content": large_content},
            {"role": "assistant", "content": large_content},
        ]

        # Should handle large content without memory issues
        result = self.reflector.analyze_session(memory_test_messages)
        assert result is not None
        assert result.get("metrics", {}).get("total_messages") == 2


if __name__ == "__main__":
    # Run tests manually if needed
    pytest.main([__file__, "-v"])
