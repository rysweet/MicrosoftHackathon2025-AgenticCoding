"""End-to-end integration test for the complete claude-trace analysis system.

This test verifies the entire workflow from JSONL parsing through GitHub issue
creation, ensuring all components work together correctly.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from config.settings import TraceConfig
from core.orchestrator import TraceAnalyzer


class TestEndToEndWorkflow(unittest.TestCase):
    """End-to-end integration tests for the complete system."""

    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = TraceAnalyzer()
        self.temp_files = []

    def tearDown(self):
        """Clean up temporary files."""
        for temp_file in self.temp_files:
            try:
                Path(temp_file).unlink()
            except (OSError, FileNotFoundError):
                pass

    def test_complete_workflow_without_github(self):
        """Test complete workflow without GitHub integration."""
        # Create sample trace data with various improvement types
        trace_data = [
            # Code improvement
            {
                "timestamp": "2024-01-01T12:00:00Z",
                "type": "completion",
                "data": {
                    "prompt": "Fix the bug in this authentication function",
                    "completion": "Here's the fixed function with proper error handling",
                    "code_before": "def auth(user): return user.valid",
                    "code_after": "def auth(user): try: return user.valid except: return False",
                },
            },
            # Prompt improvement
            {
                "timestamp": "2024-01-01T12:01:00Z",
                "type": "completion",
                "data": {
                    "prompt": "unclear request",
                    "completion": "Could you be more specific about what you need?",
                    "clarification_needed": True,
                    "improved_prompt": "Create a Python function that validates user authentication",
                },
            },
            # System fix
            {
                "timestamp": "2024-01-01T12:02:00Z",
                "type": "error",
                "data": {
                    "error_type": "connection_timeout",
                    "error_message": "Connection timed out after 30 seconds",
                    "fix_applied": "Added retry logic with exponential backoff",
                    "success": True,
                },
            },
        ]

        # Create temporary JSONL file
        temp_file = self._create_temp_jsonl_file(trace_data)

        # Run analysis
        result = self.analyzer.analyze_single_file(temp_file, create_issues=False)

        # Verify results
        self.assertTrue(result.success, f"Analysis failed: {result.error_message}")
        self.assertEqual(result.files_processed, 1)
        self.assertEqual(result.entries_parsed, 3)
        self.assertGreater(result.patterns_identified, 0)
        self.assertGreater(result.execution_time_seconds, 0)

        # Verify detailed results
        details = result.detailed_results
        self.assertIn("patterns", details)
        self.assertIn("entries", details)
        self.assertIn("files", details)

        # Verify pattern types were identified
        pattern_types = details["patterns"]["by_type"]
        self.assertGreater(len(pattern_types), 0)

    def test_workflow_with_mocked_github(self):
        """Test complete workflow with mocked GitHub integration."""
        # Configure analyzer with GitHub credentials (will be mocked)
        analyzer = TraceAnalyzer(
            github_token="test_token", repo_owner="test_owner", repo_name="test_repo"
        )

        # Create sample trace data
        trace_data = [
            {
                "timestamp": "2024-01-01T12:00:00Z",
                "type": "completion",
                "data": {
                    "prompt": "Fix performance issue in database query",
                    "completion": "Here's the optimized query using indexing",
                    "performance_gain": "50% faster execution",
                    "optimization_type": "indexing",
                },
            }
        ]

        # Create temporary file
        temp_file = self._create_temp_jsonl_file(trace_data)

        # Mock GitHub issue creation
        with patch.object(analyzer.issue_generator.github_creator, "create_issue") as mock_create:
            from core.issue_generator import IssueCreationResult

            mock_create.return_value = IssueCreationResult(
                success=True,
                issue_number=123,
                issue_url="https://github.com/test_owner/test_repo/issues/123",
                title="Code Improvement: Optimized database query",
            )

            # Run analysis with issue creation
            result = analyzer.analyze_single_file(temp_file, create_issues=True)

        # Verify results
        self.assertTrue(result.success)
        self.assertEqual(result.issues_created, 1)

        # Verify GitHub integration was called
        mock_create.assert_called_once()
        call_args = mock_create.call_args[1]
        self.assertIn("Code Improvement", call_args["title"])
        self.assertIn("performance", call_args["body"].lower())

    def test_error_handling_invalid_file(self):
        """Test error handling with invalid files."""
        # Test with non-existent file
        result = self.analyzer.analyze_single_file("nonexistent.jsonl")
        self.assertFalse(result.success)
        self.assertIn("No valid entries found", result.error_message or "")

        # Test with invalid JSON
        invalid_json_file = self._create_temp_file("invalid json content")
        result = self.analyzer.analyze_single_file(invalid_json_file)
        self.assertFalse(result.success)

    def test_deduplication_workflow(self):
        """Test deduplication across multiple similar patterns."""
        # Create trace data with similar patterns
        trace_data = [
            {
                "timestamp": "2024-01-01T12:00:00Z",
                "type": "completion",
                "data": {
                    "prompt": "Fix authentication bug in login system",
                    "completion": "Here's the fix for the authentication issue",
                    "code_improvement": True,
                },
            },
            {
                "timestamp": "2024-01-01T12:01:00Z",
                "type": "completion",
                "data": {
                    "prompt": "Fixed authentication bug in login system",  # Very similar
                    "completion": "The authentication issue has been resolved",
                    "code_improvement": True,
                },
            },
        ]

        temp_file = self._create_temp_jsonl_file(trace_data)
        result = self.analyzer.analyze_single_file(temp_file, create_issues=False)

        # Should identify patterns but deduplicate them
        self.assertTrue(result.success)
        self.assertGreater(result.patterns_identified, 0)
        # Should have fewer unique patterns due to deduplication
        self.assertLessEqual(result.unique_patterns, result.patterns_identified)

        # Check deduplication stats
        dedup_report = self.analyzer.deduplication_engine.get_deduplication_report()
        self.assertGreater(dedup_report["total_patterns_checked"], 0)

    def test_configuration_integration(self):
        """Test configuration system integration."""
        # Create custom configuration
        custom_config = TraceConfig(
            {
                "analysis": {"similarity_threshold": 0.9, "min_confidence_threshold": 0.8},
                "github": {"daily_issue_limit": 25, "hourly_issue_limit": 5},
            }
        )

        # Verify configuration is applied
        self.assertEqual(custom_config.analysis.similarity_threshold, 0.9)
        self.assertEqual(custom_config.github.daily_issue_limit, 25)

        # Test configuration validation
        with self.assertRaises(ValueError):
            TraceConfig(
                {
                    "analysis": {
                        "similarity_threshold": 1.5  # Invalid value
                    }
                }
            )

    def test_multiple_file_analysis(self):
        """Test analysis of multiple trace files."""
        # Create multiple trace files
        files_data = [
            # File 1: Code improvements
            [
                {
                    "timestamp": "2024-01-01T12:00:00Z",
                    "type": "completion",
                    "data": {
                        "prompt": "Fix bug in validation function",
                        "completion": "Added null check and error handling",
                        "code_improvement": True,
                    },
                }
            ],
            # File 2: System fixes
            [
                {
                    "timestamp": "2024-01-01T12:05:00Z",
                    "type": "error",
                    "data": {
                        "error_type": "memory_leak",
                        "fix_applied": "Implemented proper cleanup",
                        "memory_usage_reduced": "60%",
                    },
                }
            ],
        ]

        temp_files = []
        for file_data in files_data:
            temp_file = self._create_temp_jsonl_file(file_data)
            temp_files.append(temp_file)

        # Analyze multiple files
        result = self.analyzer.analyze_trace_files(temp_files, create_issues=False)

        # Verify results
        self.assertTrue(result.success)
        self.assertEqual(result.files_processed, 2)
        self.assertEqual(result.entries_parsed, 2)
        self.assertGreater(result.patterns_identified, 0)

        # Clean up
        for temp_file in temp_files:
            Path(temp_file).unlink()

    def test_analysis_summary_and_statistics(self):
        """Test analysis summary and statistics generation."""
        # Create trace data
        trace_data = [
            {
                "timestamp": "2024-01-01T12:00:00Z",
                "type": "completion",
                "data": {
                    "prompt": "Optimize database performance",
                    "completion": "Implemented caching solution",
                    "performance_improvement": True,
                },
            }
        ]

        temp_file = self._create_temp_jsonl_file(trace_data)

        # Run analysis
        result = self.analyzer.analyze_single_file(temp_file, create_issues=False)
        self.assertTrue(result.success)

        # Test analysis summary
        summary = self.analyzer.get_analysis_summary()
        self.assertIn("last_analysis", summary)
        self.assertIn("component_statistics", summary)
        self.assertIn("github_integration_enabled", summary)

        # Test result conversion to dict
        result_dict = result.to_dict()
        self.assertIn("success", result_dict)
        self.assertIn("summary", result_dict)
        self.assertIn("detailed_results", result_dict)

    def _create_temp_jsonl_file(self, data):
        """Create a temporary JSONL file with the given data."""
        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
        for entry in data:
            temp_file.write(json.dumps(entry) + "\n")
        temp_file.close()
        self.temp_files.append(temp_file.name)
        return temp_file.name

    def _create_temp_file(self, content):
        """Create a temporary file with arbitrary content."""
        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
        temp_file.write(content)
        temp_file.close()
        self.temp_files.append(temp_file.name)
        return temp_file.name


if __name__ == "__main__":
    unittest.main()
