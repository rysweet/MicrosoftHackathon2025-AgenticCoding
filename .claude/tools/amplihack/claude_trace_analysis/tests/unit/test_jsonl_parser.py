"""Unit tests for JSONL Parser module.

Tests the pure parsing functionality with no side effects.
Follows TDD approach - tests written before implementation.
"""

import json
import unittest
from pathlib import Path
from unittest.mock import mock_open, patch

from ...core.jsonl_parser import JSONLParser, ParsedEntry, ValidationError


class TestJSONLParser(unittest.TestCase):
    """Test cases for JSONLParser following TDD approach."""

    def setUp(self):
        """Set up test fixtures."""
        self.parser = JSONLParser()

    def test_parse_valid_single_entry(self):
        """Should parse a single valid JSONL entry."""
        jsonl_content = '{"timestamp": "2024-01-01T12:00:00", "type": "completion", "data": {"prompt": "test"}}\n'

        with patch("builtins.open", mock_open(read_data=jsonl_content)):
            entries = self.parser.parse_file("test.jsonl")

        self.assertEqual(len(entries), 1)
        self.assertIsInstance(entries[0], ParsedEntry)
        self.assertEqual(entries[0].timestamp, "2024-01-01T12:00:00")
        self.assertEqual(entries[0].entry_type, "completion")
        self.assertEqual(entries[0].data["prompt"], "test")

    def test_parse_multiple_entries(self):
        """Should parse multiple JSONL entries."""
        jsonl_content = (
            '{"timestamp": "2024-01-01T12:00:00", "type": "completion", "data": {"prompt": "test1"}}\n'
            '{"timestamp": "2024-01-01T12:01:00", "type": "completion", "data": {"prompt": "test2"}}\n'
        )

        with patch("builtins.open", mock_open(read_data=jsonl_content)):
            entries = self.parser.parse_file("test.jsonl")

        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].data["prompt"], "test1")
        self.assertEqual(entries[1].data["prompt"], "test2")

    def test_parse_empty_file(self):
        """Should handle empty files gracefully."""
        with patch("builtins.open", mock_open(read_data="")):
            entries = self.parser.parse_file("empty.jsonl")

        self.assertEqual(len(entries), 0)

    def test_parse_invalid_json(self):
        """Should raise ValidationError for invalid JSON."""
        invalid_json = '{"invalid": json malformed}\n'

        with patch("builtins.open", mock_open(read_data=invalid_json)):
            with self.assertRaises(ValidationError) as context:
                self.parser.parse_file("invalid.jsonl")

        self.assertIn("Invalid JSON on line 1", str(context.exception))

    def test_parse_missing_required_fields(self):
        """Should raise ValidationError for missing required fields."""
        missing_fields = '{"timestamp": "2024-01-01T12:00:00"}\n'  # Missing type and data

        with patch("builtins.open", mock_open(read_data=missing_fields)):
            with self.assertRaises(ValidationError) as context:
                self.parser.parse_file("missing.jsonl")

        self.assertIn("Missing required field", str(context.exception))

    def test_validate_file_size_limit(self):
        """Should enforce file size limits for security."""
        # Mock a file that exceeds size limit
        with patch("pathlib.Path.stat") as mock_stat:
            mock_stat.return_value.st_size = 101 * 1024 * 1024  # 101MB > 100MB limit

            with self.assertRaises(ValidationError) as context:
                self.parser.parse_file("large.jsonl")

        self.assertIn("File size exceeds limit", str(context.exception))

    def test_validate_entry_count_limit(self):
        """Should enforce entry count limits for performance."""
        # Create content with too many entries
        jsonl_content = (
            "\n".join(
                [
                    '{"timestamp": "2024-01-01T12:00:00", "type": "completion", "data": {"prompt": "test"}}'
                    for _ in range(10001)  # 10001 > 10000 limit
                ]
            )
            + "\n"
        )

        with patch("builtins.open", mock_open(read_data=jsonl_content)):
            with self.assertRaises(ValidationError) as context:
                self.parser.parse_file("too_many.jsonl")

        self.assertIn("Too many entries", str(context.exception))

    def test_path_traversal_protection(self):
        """Should prevent path traversal attacks."""
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\SAM",
        ]

        for path in malicious_paths:
            with self.assertRaises(ValidationError) as context:
                self.parser.parse_file(path)

            self.assertIn("Invalid file path", str(context.exception))

    def test_parse_entry_with_performance_requirements(self):
        """Should parse large files within performance requirements (<5 seconds for 10K entries)."""
        import time

        # Create 10K entries
        jsonl_content = (
            "\n".join(
                [
                    '{"timestamp": "2024-01-01T12:00:00", "type": "completion", "data": {"prompt": "test"}}'
                    for _ in range(10000)
                ]
            )
            + "\n"
        )

        with patch("builtins.open", mock_open(read_data=jsonl_content)):
            start_time = time.time()
            entries = self.parser.parse_file("performance.jsonl")
            end_time = time.time()

        self.assertEqual(len(entries), 10000)
        self.assertLess(end_time - start_time, 5.0, "Parsing should complete within 5 seconds")

    def test_schema_validation(self):
        """Should validate entry schema according to claude-trace format."""
        # Valid claude-trace entry
        valid_entry = {
            "timestamp": "2024-01-01T12:00:00Z",
            "type": "completion",
            "data": {
                "model": "claude-3",
                "prompt": "test prompt",
                "completion": "test completion",
                "tokens": {"input": 10, "output": 15},
            },
        }

        jsonl_content = json.dumps(valid_entry) + "\n"

        with patch("builtins.open", mock_open(read_data=jsonl_content)):
            entries = self.parser.parse_file("valid_schema.jsonl")

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].entry_type, "completion")

    def test_batch_processing_capability(self):
        """Should handle batch processing of multiple files."""
        files = ["file1.jsonl", "file2.jsonl"]
        file_contents = {
            "file1.jsonl": '{"timestamp": "2024-01-01T12:00:00", "type": "completion", "data": {"prompt": "test1"}}\n',
            "file2.jsonl": '{"timestamp": "2024-01-01T12:00:00", "type": "completion", "data": {"prompt": "test2"}}\n',
        }

        def mock_open_func(filename, *args, **kwargs):
            return mock_open(read_data=file_contents[filename])()

        with patch("builtins.open", side_effect=mock_open_func):
            with patch("pathlib.Path.stat") as mock_stat:
                mock_stat.return_value.st_size = 1024  # Small file size
                all_entries = self.parser.parse_files([Path(f) for f in files])

        self.assertEqual(len(all_entries), 2)


class TestParsedEntry(unittest.TestCase):
    """Test cases for ParsedEntry data model."""

    def test_parsed_entry_creation(self):
        """Should create ParsedEntry with required fields."""
        entry = ParsedEntry(
            timestamp="2024-01-01T12:00:00", entry_type="completion", data={"prompt": "test"}
        )

        self.assertEqual(entry.timestamp, "2024-01-01T12:00:00")
        self.assertEqual(entry.entry_type, "completion")
        self.assertEqual(entry.data["prompt"], "test")

    def test_parsed_entry_validation(self):
        """Should validate ParsedEntry fields."""
        with self.assertRaises(ValueError):
            ParsedEntry(timestamp="", entry_type="completion", data={})

        with self.assertRaises(ValueError):
            ParsedEntry(timestamp="2024-01-01T12:00:00", entry_type="", data={})


if __name__ == "__main__":
    unittest.main()
