#!/usr/bin/env python3
"""
Test suite for CodebaseAnalyzer following TDD requirements:
- 60% unit tests
- 30% integration tests
- 10% end-to-end tests
"""

import json
import shutil

# Add project root to path for imports
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from tool import CodebaseAnalyzer


class TestCodebaseAnalyzer:
    """Test suite for CodebaseAnalyzer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.analyzer = CodebaseAnalyzer()

        # Create sample files for testing
        (self.temp_dir / "sample.py").write_text("""
def hello_world():
    '''Simple hello world function'''
    print("Hello, World!")

if __name__ == "__main__":
    hello_world()
        """)

        (self.temp_dir / "config.yaml").write_text("""
app:
  name: test
  version: 1.0
        """)

        (self.temp_dir / "README.md").write_text("# Test Project\n\nSample project for testing.")

        # Create subdirectory with more files
        (self.temp_dir / "src").mkdir()
        (self.temp_dir / "src" / "main.py").write_text("""
class DataProcessor:
    def __init__(self):
        self.data = []

    def process(self, item):
        # TODO: Add input validation
        self.data.append(item)
        return item * 2
        """)

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # ===================
    # UNIT TESTS (60%)
    # ===================

    def test_validate_input_valid_directory(self):
        """Test input validation with valid directory."""
        result = self.analyzer._validate_input(str(self.temp_dir))
        assert result == self.temp_dir.resolve()

    def test_validate_input_valid_file(self):
        """Test input validation with valid file."""
        test_file = self.temp_dir / "sample.py"
        result = self.analyzer._validate_input(str(test_file))
        assert result == test_file.resolve()

    def test_validate_input_nonexistent_path(self):
        """Test input validation catches nonexistent paths."""
        with pytest.raises(ValueError, match="Target path does not exist"):
            self.analyzer._validate_input("/nonexistent/path")

    def test_validate_input_directory_traversal(self):
        """Test security validation prevents directory traversal."""
        with pytest.raises(ValueError, match="Directory traversal not allowed"):
            self.analyzer._validate_input("../../../etc/passwd")

    def test_discover_content_python_files(self):
        """Test content discovery finds Python files correctly."""
        content_map = self.analyzer._discover_content(self.temp_dir)
        assert "python" in content_map
        assert len(content_map["python"]) == 2  # sample.py and src/main.py

    def test_discover_content_yaml_files(self):
        """Test content discovery finds YAML files correctly."""
        content_map = self.analyzer._discover_content(self.temp_dir)
        assert "yaml" in content_map
        assert len(content_map["yaml"]) == 1  # config.yaml

    def test_discover_content_markdown_files(self):
        """Test content discovery finds Markdown files correctly."""
        content_map = self.analyzer._discover_content(self.temp_dir)
        assert "markdown" in content_map
        assert len(content_map["markdown"]) == 1  # README.md

    def test_discover_content_single_file(self):
        """Test content discovery with single file input."""
        test_file = self.temp_dir / "sample.py"
        content_map = self.analyzer._discover_content(test_file)
        assert "python" in content_map
        assert len(content_map["python"]) == 1
        assert content_map["python"][0] == test_file

    def test_should_skip_file_git_directory(self):
        """Test file skipping for git directories."""
        git_file = self.temp_dir / ".git" / "config"
        git_file.parent.mkdir()
        git_file.write_text("test")
        assert self.analyzer._should_skip_file(git_file) is True

    def test_should_skip_file_pycache(self):
        """Test file skipping for Python cache directories."""
        cache_file = self.temp_dir / "__pycache__" / "test.pyc"
        cache_file.parent.mkdir()
        cache_file.write_text("test")
        assert self.analyzer._should_skip_file(cache_file) is True

    def test_should_skip_file_normal_file(self):
        """Test file skipping allows normal files."""
        normal_file = self.temp_dir / "normal.py"
        normal_file.write_text("print('hello')")
        assert self.analyzer._should_skip_file(normal_file) is False

    def test_estimate_lines_calculation(self):
        """Test line estimation calculation."""
        content_map = {"python": [self.temp_dir / "sample.py"]}
        lines = self.analyzer._estimate_lines(content_map)
        assert lines > 0
        assert isinstance(lines, int)

    def test_select_agents_includes_all_default(self):
        """Test agent selection includes all default agents."""
        content_map = {"python": [Path("test.py")]}
        agents = self.analyzer._select_agents(content_map, {})
        expected_agents = ["analyzer", "security", "optimizer", "patterns"]
        for agent in expected_agents:
            assert agent in agents

    def test_prepare_options_with_defaults(self):
        """Test option preparation applies defaults."""
        options = self.analyzer._prepare_options({})
        assert options["format"] == "text"
        assert options["depth"] == "deep"
        assert options["verbose"] is False

    def test_prepare_options_with_overrides(self):
        """Test option preparation preserves user overrides."""
        user_options = {"format": "json", "verbose": True}
        options = self.analyzer._prepare_options(user_options)
        assert options["format"] == "json"
        assert options["verbose"] is True
        assert options["depth"] == "deep"  # Default preserved

    def test_prepare_options_invalid_format(self):
        """Test option validation catches invalid format."""
        with pytest.raises(ValueError, match="Invalid format"):
            self.analyzer._prepare_options({"format": "invalid"})

    def test_prepare_options_invalid_depth(self):
        """Test option validation catches invalid depth."""
        with pytest.raises(ValueError, match="Invalid depth"):
            self.analyzer._prepare_options({"depth": "invalid"})

    def test_prioritize_findings_by_type(self):
        """Test findings prioritization by type."""
        findings = [
            {"type": "info", "message": "Info finding"},
            {"type": "security", "message": "Security finding"},
            {"type": "performance", "message": "Performance finding"},
        ]
        prioritized = self.analyzer._prioritize_findings(findings)
        assert prioritized[0]["type"] == "security"
        assert prioritized[1]["type"] == "performance"
        assert prioritized[2]["type"] == "info"

    def test_prioritize_recommendations_by_keywords(self):
        """Test recommendation prioritization by keywords."""
        recommendations = [
            "Add more documentation",
            "Fix security vulnerability",
            "Optimize performance bottleneck",
            "Add input validation",
        ]
        prioritized = self.analyzer._prioritize_recommendations(recommendations)
        # Security and validation should be prioritized
        assert "security" in prioritized[0].lower() or "validation" in prioritized[0].lower()

    def test_format_output_json_format(self):
        """Test JSON output formatting."""
        result = {"test": "data", "summary": {"agents_run": 1}}
        formatted = self.analyzer._format_output(result, {"format": "json"})
        assert formatted == result
        assert isinstance(formatted, dict)

    def test_format_output_text_format(self):
        """Test text output formatting."""
        result = {
            "timestamp": "2023-01-01T00:00:00",
            "execution_time": 1.5,
            "summary": {"agents_run": 1, "total_findings": 2, "metrics": {"files_analyzed": 5}},
            "recommendations": ["Test recommendation"],
        }
        formatted = self.analyzer._format_output(result, {"format": "text"})
        assert isinstance(formatted, str)
        assert "Analyzing codebase" in formatted
        assert "Summary:" in formatted

    def test_format_output_invalid_format(self):
        """Test output formatting with invalid format."""
        result = {"test": "data"}
        with pytest.raises(ValueError, match="Unsupported format"):
            self.analyzer._format_output(result, {"format": "invalid"})

    def test_empty_result_structure(self):
        """Test empty result has correct structure."""
        result = self.analyzer._empty_result("Test message")
        assert "timestamp" in result
        assert "execution_time" in result
        assert "summary" in result
        assert result["summary"]["message"] == "Test message"
        assert result["summary"]["agents_run"] == 0

    # ===================
    # INTEGRATION TESTS (30%)
    # ===================

    def test_configuration_loading_and_usage(self):
        """Test configuration system integration."""
        custom_config = {"max_file_size": 500000, "skip_patterns": [".test", ".custom"]}
        analyzer = CodebaseAnalyzer(custom_config)
        assert analyzer.config["max_file_size"] == 500000
        assert ".test" in analyzer.config["skip_patterns"]

    def test_analysis_with_no_content_found(self):
        """Test analysis behavior when no analyzable content found."""
        empty_dir = self.temp_dir / "empty"
        empty_dir.mkdir()

        result = self.analyzer.analyze(str(empty_dir))
        assert "No analyzable content found" in result["summary"]["message"]
        assert result["summary"]["agents_run"] == 0

    def test_analysis_with_mixed_content_types(self):
        """Test analysis handles mixed content types correctly."""
        # Add more file types
        (self.temp_dir / "script.js").write_text("console.log('hello');")
        (self.temp_dir / "data.json").write_text('{"key": "value"}')

        result = self.analyzer.analyze(str(self.temp_dir))

        assert isinstance(result, dict)
        assert "summary" in result
        assert "findings" in result
        assert "recommendations" in result
        assert result["summary"]["agents_run"] > 0

    def test_analysis_output_format_consistency(self):
        """Test analysis output format consistency across runs."""
        result1 = self.analyzer.analyze(str(self.temp_dir), {"format": "json"})
        result2 = self.analyzer.analyze(str(self.temp_dir), {"format": "json"})

        # Structure should be consistent
        assert set(result1.keys()) == set(result2.keys())
        assert set(result1["summary"].keys()) == set(result2["summary"].keys())

    def test_agent_execution_and_result_aggregation(self):
        """Test that agents are executed and results properly aggregated."""
        result = self.analyzer.analyze(str(self.temp_dir))

        # Verify agent execution
        assert result["summary"]["agents_run"] > 0
        assert "agent_details" in result
        assert len(result["agent_details"]) > 0

        # Verify result aggregation
        for agent_detail in result["agent_details"]:
            assert "name" in agent_detail
            assert "execution_time" in agent_detail
            assert "metrics" in agent_detail

    def test_security_validation_integration(self):
        """Test security validation is properly integrated."""
        # Test that security measures are in place
        with pytest.raises(ValueError):
            self.analyzer.analyze("../../../etc/passwd")

        # Test that normal paths work
        result = self.analyzer.analyze(str(self.temp_dir))
        assert "summary" in result

    def test_error_handling_in_analysis_pipeline(self):
        """Test error handling throughout analysis pipeline."""
        # Create a scenario that might cause issues (permission denied)
        restricted_dir = self.temp_dir / "restricted"
        restricted_dir.mkdir()
        restricted_file = restricted_dir / "restricted.py"
        restricted_file.write_text("test")

        # Analysis should handle this gracefully
        result = self.analyzer.analyze(str(self.temp_dir))
        assert isinstance(result, dict)
        assert "summary" in result

    def test_metrics_aggregation_across_agents(self):
        """Test that metrics are properly aggregated across agents."""
        result = self.analyzer.analyze(str(self.temp_dir))

        # Check that summary metrics exist
        assert "metrics" in result["summary"]
        summary_metrics = result["summary"]["metrics"]

        # Should have aggregated metrics from multiple agents
        assert len(summary_metrics) > 0

        # All metric values should be numbers
        for metric, value in summary_metrics.items():
            assert isinstance(value, (int, float))

    # ===================
    # END-TO-END TESTS (10%)
    # ===================

    def test_full_analysis_workflow_text_output(self):
        """Test complete analysis workflow with text output."""
        # Create a realistic project structure
        (self.temp_dir / "requirements.txt").write_text("requests==2.25.1\nflask==2.0.1")
        (self.temp_dir / "tests").mkdir()
        (self.temp_dir / "tests" / "test_main.py").write_text("""
import unittest
from src.main import DataProcessor

class TestDataProcessor(unittest.TestCase):
    def test_process(self):
        processor = DataProcessor()
        result = processor.process(5)
        self.assertEqual(result, 10)
        """)

        # Run full analysis
        result = self.analyzer.analyze(str(self.temp_dir), {"format": "text"})

        # Verify complete text output
        assert isinstance(result, str)
        assert "Analyzing codebase" in result
        assert "Summary:" in result
        assert "Recommendations:" in result

        # Should mention key findings
        assert "Files analyzed:" in result
        assert "Total lines:" in result

    def test_full_analysis_workflow_json_output(self):
        """Test complete analysis workflow with JSON output."""
        # Add more comprehensive project structure
        docs_dir = self.temp_dir / "docs"
        docs_dir.mkdir()
        (docs_dir / "api.md").write_text("# API Documentation")

        # Run full analysis with JSON output
        result = self.analyzer.analyze(str(self.temp_dir), {"format": "json"})

        # Verify complete JSON structure
        assert isinstance(result, dict)

        # Verify all required sections
        required_keys = [
            "timestamp",
            "execution_time",
            "summary",
            "findings",
            "recommendations",
            "agent_details",
        ]
        for key in required_keys:
            assert key in result

        # Verify summary structure
        summary = result["summary"]
        assert "agents_run" in summary
        assert "total_findings" in summary
        assert "metrics" in summary

        # Verify agent details
        assert len(result["agent_details"]) > 0
        for agent in result["agent_details"]:
            assert "name" in agent
            assert "execution_time" in agent
            assert "metrics" in agent

    def test_command_line_interface_simulation(self):
        """Test command-line interface behavior simulation."""
        from ..tool import main

        # Test that main function exists and can be called
        # (In real scenario, would test with subprocess or argument mocking)
        assert callable(main)

        # Test error handling in main
        with patch("sys.argv", ["tool.py", "/nonexistent/path"]):
            with patch("sys.stderr"):
                result = main()
                assert result == 1  # Should return error code

    def test_analysis_performance_with_large_project(self):
        """Test analysis performance with larger project structure."""
        # Create larger project structure
        for i in range(20):
            (self.temp_dir / f"module_{i}.py").write_text(f"""
def function_{i}():
    '''Function {i} implementation'''
    return {i} * 2

class Class{i}:
    def __init__(self):
        self.value = {i}

    def method(self):
        return self.value * 3
            """)

        # Run analysis and measure basic performance
        import time

        start_time = time.time()
        result = self.analyzer.analyze(str(self.temp_dir))
        end_time = time.time()

        # Should complete in reasonable time (less than 30 seconds for test)
        execution_time = end_time - start_time
        assert execution_time < 30

        # Should still produce valid results
        assert isinstance(result, dict)
        assert result["summary"]["agents_run"] > 0
        assert len(result["findings"]) > 0

    def test_file_output_integration(self):
        """Test file output integration works correctly."""
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as output_file:
            output_path = output_file.name

        try:
            # Analyze with JSON output to file
            result = self.analyzer.analyze(str(self.temp_dir), {"format": "json"})

            # Write to file (simulating CLI behavior)
            with open(output_path, "w") as f:
                json.dump(result, f, indent=2)

            # Verify file was written correctly
            with open(output_path, "r") as f:
                loaded_result = json.load(f)

            assert loaded_result == result

        finally:
            # Clean up
            Path(output_path).unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
