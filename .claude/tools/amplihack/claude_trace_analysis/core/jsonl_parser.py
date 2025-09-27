"""Pure JSONL parsing with validation and security measures.

This module provides secure parsing of claude-trace JSONL files with:
- Input validation and sanitization
- File size and entry count limits
- Path traversal protection
- Schema validation
- Performance requirements (<5 seconds for 10K entries)
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Union


class ValidationError(Exception):
    """Raised when JSONL validation fails."""

    pass


@dataclass
class ParsedEntry:
    """Represents a parsed claude-trace entry with validation.

    Attributes:
        timestamp: ISO 8601 timestamp string
        entry_type: Type of entry (completion, tool_use, etc.)
        data: Entry payload data
        source_file: Optional source file path
        line_number: Optional line number in source file
    """

    timestamp: str
    entry_type: str
    data: Dict[str, Any]
    source_file: str = ""
    line_number: int = 0

    def __post_init__(self):
        """Validate fields after initialization."""
        if not self.timestamp or not isinstance(self.timestamp, str):
            raise ValueError("timestamp must be a non-empty string")

        if not self.entry_type or not isinstance(self.entry_type, str):
            raise ValueError("entry_type must be a non-empty string")

        if not isinstance(self.data, dict):
            raise ValueError("data must be a dictionary")


class JSONLParser:
    """Secure JSONL parser for claude-trace logs.

    Provides pure parsing functionality with no side effects:
    - Security validation (file size, path traversal)
    - Performance optimization for large files
    - Schema validation for claude-trace format
    - Comprehensive error handling
    """

    # Security limits
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    MAX_ENTRIES = 10000  # Performance limit

    # Required fields for claude-trace entries
    REQUIRED_FIELDS = {"timestamp", "type", "data"}

    # Path traversal protection patterns
    DANGEROUS_PATH_PATTERNS = [
        r"\.\.[\\/]",  # Parent directory traversal
        r"^[\\/]",  # Absolute paths
        r"^[A-Za-z]:[\\/]",  # Windows drive paths
        r"[\\/]etc[\\/]",  # Unix system directories
        r"[\\/]windows[\\/]",  # Windows system directories
    ]

    def __init__(self):
        """Initialize the parser with security patterns."""
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.DANGEROUS_PATH_PATTERNS
        ]

    def parse_file(self, file_path: Union[str, Path]) -> List[ParsedEntry]:
        """Parse a single JSONL file with security validation.

        Args:
            file_path: Path to the JSONL file to parse

        Returns:
            List of ParsedEntry objects

        Raises:
            ValidationError: If file validation fails
            FileNotFoundError: If file doesn't exist
        """
        file_path = Path(file_path)

        # Security validation
        self._validate_file_path(str(file_path))
        self._validate_file_size(file_path)

        entries = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:  # Skip empty lines
                        continue

                    # Check entry count limit
                    if len(entries) >= self.MAX_ENTRIES:
                        raise ValidationError(
                            f"Too many entries: exceeds limit of {self.MAX_ENTRIES}"
                        )

                    try:
                        entry_data = json.loads(line)
                    except json.JSONDecodeError as e:
                        raise ValidationError(f"Invalid JSON on line {line_num}: {str(e)}")

                    # Validate required fields
                    self._validate_entry_schema(entry_data, line_num)

                    # Create parsed entry
                    parsed_entry = ParsedEntry(
                        timestamp=entry_data["timestamp"],
                        entry_type=entry_data["type"],
                        data=entry_data["data"],
                        source_file=str(file_path),
                        line_number=line_num,
                    )

                    entries.append(parsed_entry)

        except (OSError, IOError) as e:
            raise ValidationError(f"File I/O error: {str(e)}")

        return entries

    def parse_files(self, file_paths: List[Union[str, Path]]) -> List[ParsedEntry]:
        """Parse multiple JSONL files in batch.

        Args:
            file_paths: List of file paths to parse

        Returns:
            Combined list of ParsedEntry objects from all files

        Raises:
            ValidationError: If any file validation fails
        """
        all_entries = []

        for file_path in file_paths:
            entries = self.parse_file(file_path)
            all_entries.extend(entries)

        return all_entries

    def _validate_file_path(self, file_path: str) -> None:
        """Validate file path for security threats.

        Args:
            file_path: File path to validate

        Raises:
            ValidationError: If path contains dangerous patterns
        """
        for pattern in self.compiled_patterns:
            if pattern.search(file_path):
                raise ValidationError(
                    f"Invalid file path: potential security risk in '{file_path}'"
                )

    def _validate_file_size(self, file_path: Path) -> None:
        """Validate file size is within limits.

        Args:
            file_path: Path object to check

        Raises:
            ValidationError: If file is too large
        """
        try:
            file_size = file_path.stat().st_size
            if file_size > self.MAX_FILE_SIZE:
                raise ValidationError(
                    f"File size exceeds limit: {file_size} bytes > {self.MAX_FILE_SIZE} bytes"
                )
        except OSError as e:
            raise ValidationError(f"Cannot access file: {str(e)}")

    def _validate_entry_schema(self, entry_data: Dict[str, Any], line_num: int) -> None:
        """Validate entry has required fields and basic structure.

        Args:
            entry_data: Parsed JSON data for the entry
            line_num: Line number for error reporting

        Raises:
            ValidationError: If schema validation fails
        """
        if not isinstance(entry_data, dict):
            raise ValidationError(f"Line {line_num}: Entry must be a JSON object")

        # Check required fields
        missing_fields = self.REQUIRED_FIELDS - set(entry_data.keys())
        if missing_fields:
            raise ValidationError(f"Line {line_num}: Missing required field(s): {missing_fields}")

        # Validate field types
        if not isinstance(entry_data.get("timestamp"), str):
            raise ValidationError(f"Line {line_num}: 'timestamp' must be a string")

        if not isinstance(entry_data.get("type"), str):
            raise ValidationError(f"Line {line_num}: 'type' must be a string")

        if not isinstance(entry_data.get("data"), dict):
            raise ValidationError(f"Line {line_num}: 'data' must be an object")
