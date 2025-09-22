#!/usr/bin/env python3
"""
Integration tests for stop hook automation system.
Tests reflection triggers automation, automation failure handling, and workflow integration.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestStopHookAutomation:
    """Test integration between stop hook and automation system"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()

        # Mock environment for testing
        self.original_env = os.environ.copy()
        os.environ["CLAUDE_REFLECTION_MODE"] = "0"  # Enable reflection

    def teardown_method(self):
        """Cleanup test environment"""
        # Restore environment
        os.environ.clear()
        os.environ.update(self.original_env)

        # Cleanup temp directory
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_reflection_triggers_automation(self):
        """Test that reflection analysis triggers automation when patterns are detected"""
        # Create messages that should trigger automation
        messages_with_patterns = [
            {"role": "user", "content": "I need to check these files"},
            {"role": "assistant", "content": "I'll help you check the files."},
            {
                "role": "assistant",
                "content": '<function_calls><invoke name="Bash"><parameter name="command">ls file1.py</parameter></invoke></function_calls>',
            },
            {
                "role": "assistant",
                "content": '<function_calls><invoke name="Bash"><parameter name="command">ls file2.py</parameter></invoke></function_calls>',
            },
            {
                "role": "assistant",
                "content": '<function_calls><invoke name="Bash"><parameter name="command">ls file3.py</parameter></invoke></function_calls>',
            },
            {
                "role": "assistant",
                "content": '<function_calls><invoke name="Bash"><parameter name="command">ls file4.py</parameter></invoke></function_calls>',
            },
            {"role": "user", "content": "This is still not working, I'm getting confused"},
            {"role": "assistant", "content": "Let me try a different approach"},
            {"role": "user", "content": "Why isn't this working? This seems broken"},
        ]

        # Mock automation pipeline to avoid actual GitHub operations
        with patch("builtins.asyncio") as mock_asyncio:
            mock_asyncio.run = Mock(return_value="test_workflow_123")

            with patch(
                ".claude.tools.reflection_automation_pipeline.ReflectionAutomationPipeline"
            ) as mock_pipeline_class:
                mock_pipeline = Mock()
                mock_pipeline.process_reflection_result = AsyncMock(
                    return_value="test_workflow_123"
                )
                mock_pipeline_class.return_value = mock_pipeline

                # Test automation opportunity check
                result = check_automation_opportunity(messages_with_patterns)

                # Should trigger automation due to repeated bash usage and user frustration
                assert result is not None
                assert result["decision"] == "continue"
                assert result["reason"] == "automation_triggered"
                assert "workflow_id" in result
                assert "automation_context" in result

    def test_automation_failure_handling(self):
        """Test handling when automation fails to trigger"""
        # Create messages with patterns but mock automation failure
        messages_with_patterns = [
            {"role": "user", "content": "Test automation failure"},
            {"role": "assistant", "content": '<function_calls><invoke name="Bash">'},
            {"role": "assistant", "content": '<function_calls><invoke name="Bash">'},
            {"role": "assistant", "content": '<function_calls><invoke name="Bash">'},
            {"role": "assistant", "content": '<function_calls><invoke name="Bash">'},
        ]

        # Mock automation to fail
        with patch(
            ".claude.tools.reflection_automation_pipeline.ReflectionAutomationPipeline"
        ) as mock_pipeline_class:
            mock_pipeline = Mock()
            mock_pipeline.process_reflection_result = AsyncMock(
                return_value=None
            )  # Automation fails
            mock_pipeline_class.return_value = mock_pipeline

            with patch("builtins.asyncio") as mock_asyncio:
                mock_asyncio.run = Mock(return_value=None)

                result = check_automation_opportunity(messages_with_patterns)

                # Should handle failure gracefully
                assert result is None  # No continuation when automation fails

    def test_workflow_integration(self):
        """Test integration with workflow system"""
        # Test that enhanced_should_continue integrates with basic continuation
        messages = [
            {"role": "user", "content": "Simple request"},
            {"role": "assistant", "content": "Simple response"},
        ]

        # Mock basic continuation to return False (no basic continuation needed)
        with patch(
            ".claude.tools.amplihack.hooks.stop_azure_continuation.should_continue"
        ) as mock_basic:
            mock_basic.return_value = False

            # Mock automation to not trigger
            with patch(
                ".claude.tools.amplihack.hooks.stop_unified.UnifiedStopHook.trigger_automation_if_needed"
            ) as mock_auto:
                mock_auto.return_value = None

                result = enhanced_should_continue(messages)

                # Should allow stop when no continuation is needed
                assert result["decision"] == "stop"
                assert result["reason"] == "no_continuation_needed"

    def test_basic_continuation_priority(self):
        """Test that basic continuation takes priority over automation"""
        messages = [
            {"role": "user", "content": "Test basic priority"},
        ]

        # Mock basic continuation to return True
        with patch(
            ".claude.tools.amplihack.hooks.stop_azure_continuation.should_continue"
        ) as mock_basic:
            mock_basic.return_value = True

            result = enhanced_should_continue(messages)

            # Should use basic continuation without checking automation
            assert result["decision"] == "continue"
            assert result["reason"] == "basic_continuation"

    def test_automation_availability_check(self):
        """Test behavior when automation is not available"""
        # This tests the fallback behavior when imports fail

        messages_with_patterns = [
            {"role": "user", "content": "Test without automation"},
            {"role": "assistant", "content": '<function_calls><invoke name="Bash">'},
            {"role": "assistant", "content": '<function_calls><invoke name="Bash">'},
            {"role": "assistant", "content": '<function_calls><invoke name="Bash">'},
        ]

        # Test with automation not available
        with patch(
            ".claude.tools.amplihack.hooks.stop_unified.UnifiedStopHook.config",
            {"enable_automation": False},
        ):
            with patch(
                ".claude.tools.amplihack.hooks.stop_azure_continuation.should_continue"
            ) as mock_basic:
                mock_basic.return_value = False

                result = enhanced_should_continue(messages_with_patterns)

                # Should fall back to stop when automation not available
                assert result["decision"] == "stop"
                assert result["reason"] == "no_continuation_needed"

    def test_reflection_loop_prevention(self):
        """Test that reflection loop prevention works in integration"""
        messages = [
            {"role": "user", "content": "Test loop prevention"},
        ]

        # Set environment to prevent reflection loops
        os.environ["CLAUDE_REFLECTION_MODE"] = "1"

        result = check_automation_opportunity(messages)

        # Should return None when reflection is disabled
        assert result is None

    def test_async_context_handling(self):
        """Test handling of async context when event loop is already running"""
        messages_with_patterns = [
            {"role": "user", "content": "Test async handling"},
            {"role": "assistant", "content": '<function_calls><invoke name="Bash">'},
            {"role": "assistant", "content": '<function_calls><invoke name="Bash">'},
            {"role": "assistant", "content": '<function_calls><invoke name="Bash">'},
            {"role": "user", "content": "This doesn't work"},
        ]

        # Mock RuntimeError to simulate event loop already running
        with patch("builtins.asyncio") as mock_asyncio:
            mock_asyncio.run = Mock(side_effect=RuntimeError("Event loop is already running"))

            result = check_automation_opportunity(messages_with_patterns)

            # Should handle RuntimeError gracefully
            assert result is None  # Should return None when async fails

    def test_automation_context_information(self):
        """Test that automation context provides useful information"""
        messages_with_patterns = [
            {"role": "user", "content": "Context test"},
            {"role": "assistant", "content": '<function_calls><invoke name="Read">'},
            {"role": "assistant", "content": '<function_calls><invoke name="Read">'},
            {"role": "assistant", "content": '<function_calls><invoke name="Read">'},
            {"role": "assistant", "content": '<function_calls><invoke name="Read">'},
            {"role": "assistant", "content": '<function_calls><invoke name="Read">'},
            {"role": "user", "content": "This is frustrating, doesn't work"},
        ]

        # Mock successful automation
        with patch(
            ".claude.tools.reflection_automation_pipeline.ReflectionAutomationPipeline"
        ) as mock_pipeline_class:
            mock_pipeline = Mock()
            mock_pipeline.process_reflection_result = AsyncMock(return_value="workflow_456")
            mock_pipeline_class.return_value = mock_pipeline

            with patch("builtins.asyncio") as mock_asyncio:
                mock_asyncio.run = Mock(return_value="workflow_456")

                result = check_automation_opportunity(messages_with_patterns)

                assert result is not None

                # Check automation context
                automation_context = result.get("automation_context", {})
                assert "session_id" in automation_context
                assert "patterns_count" in automation_context
                assert "primary_pattern" in automation_context

                # Should contain useful instructions
                instructions = result.get("instructions", "")
                assert "Pattern Detected" in instructions
                assert "Automation Started" in instructions
                assert "workflow_456" in instructions

    def test_error_handling_in_automation_check(self):
        """Test error handling in automation opportunity check"""
        messages = [
            {"role": "user", "content": "Error handling test"},
        ]

        # Mock SessionReflector to raise an exception
        with patch(
            ".claude.tools.amplihack.hooks.reflection.SessionReflector"
        ) as mock_reflector_class:
            mock_reflector = Mock()
            mock_reflector.analyze_session = Mock(side_effect=Exception("Test error"))
            mock_reflector_class.return_value = mock_reflector

            result = check_automation_opportunity(messages)

            # Should handle errors gracefully and return None
            assert result is None

    def test_multiple_pattern_types_automation(self):
        """Test automation with multiple different pattern types"""
        messages_multiple_patterns = []

        # Add user messages with frustration
        messages_multiple_patterns.extend(
            [
                {"role": "user", "content": "I need help with file processing"},
                {"role": "assistant", "content": "I'll help you process the files."},
            ]
        )

        # Add repeated read operations
        for i in range(6):
            messages_multiple_patterns.append(
                {
                    "role": "assistant",
                    "content": f'<function_calls><invoke name="Read"><parameter name="file_path">file{i}.py</parameter></invoke></function_calls>',
                }
            )

        # Add error patterns
        messages_multiple_patterns.extend(
            [
                {"role": "user", "content": "Getting errors again"},
                {"role": "assistant", "content": "Let me retry that operation"},
                {"role": "user", "content": "Still getting the same error, this is broken"},
            ]
        )

        # Add long session indicators (many messages)
        for i in range(50):
            messages_multiple_patterns.extend(
                [
                    {"role": "user", "content": f"Additional request {i}"},
                    {"role": "assistant", "content": f"Additional response {i}"},
                ]
            )

        # Mock successful automation
        with patch(
            ".claude.tools.reflection_automation_pipeline.ReflectionAutomationPipeline"
        ) as mock_pipeline_class:
            mock_pipeline = Mock()
            mock_pipeline.process_reflection_result = AsyncMock(
                return_value="multi_pattern_workflow"
            )
            mock_pipeline_class.return_value = mock_pipeline

            with patch("builtins.asyncio") as mock_asyncio:
                mock_asyncio.run = Mock(return_value="multi_pattern_workflow")

                result = check_automation_opportunity(messages_multiple_patterns)

                # Should trigger automation for multiple patterns
                assert result is not None
                assert result["decision"] == "continue"
                assert result["workflow_id"] == "multi_pattern_workflow"

                # Should have automation context showing multiple patterns
                automation_context = result.get("automation_context", {})
                assert automation_context.get("patterns_count", 0) > 1


class TestIntegrationEndToEnd:
    """End-to-end integration tests"""

    def test_full_integration_flow(self):
        """Test complete flow from stop hook to automation trigger"""
        # This would test the complete flow but requires careful mocking
        # to avoid actual GitHub operations and file system changes

        messages = [
            {"role": "user", "content": "I want to process multiple files"},
            {"role": "assistant", "content": "I'll help you process the files systematically."},
        ]

        # Add repeated bash operations that should trigger automation
        for i in range(8):
            messages.append(
                {
                    "role": "assistant",
                    "content": f'<function_calls><invoke name="Bash"><parameter name="command">process_file_{i}.sh</parameter></invoke></function_calls>',
                }
            )

        messages.extend(
            [
                {"role": "user", "content": "This is taking too long and doesn't seem to work"},
                {"role": "assistant", "content": "Let me try a different approach"},
            ]
        )

        # Mock the entire pipeline
        with patch(
            ".claude.tools.amplihack.hooks.stop_azure_continuation.is_proxy_active"
        ) as mock_proxy:
            mock_proxy.return_value = True

            with patch(
                ".claude.tools.amplihack.hooks.stop_azure_continuation.should_continue"
            ) as mock_basic:
                mock_basic.return_value = False

                with patch(
                    ".claude.tools.reflection_automation_pipeline.ReflectionAutomationPipeline"
                ) as mock_pipeline_class:
                    mock_pipeline = Mock()
                    mock_pipeline.process_reflection_result = AsyncMock(
                        return_value="end_to_end_workflow"
                    )
                    mock_pipeline_class.return_value = mock_pipeline

                    with patch("builtins.asyncio") as mock_asyncio:
                        mock_asyncio.run = Mock(return_value="end_to_end_workflow")

                        result = enhanced_should_continue(messages)

                        # Should trigger automation
                        assert result["decision"] == "continue"
                        assert result["reason"] == "automation_triggered"
                        assert result["workflow_id"] == "end_to_end_workflow"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
