"""Tests for FrameworkPathResolver."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from src.amplihack.utils.paths import FrameworkPathResolver


class TestFrameworkPathResolver:
    """Test cases for FrameworkPathResolver."""

    def test_find_framework_root_local_deployment(self):
        """Test finding framework root in local deployment scenario."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            claude_dir = temp_path / ".claude"
            claude_dir.mkdir()

            # Test from subdirectory
            sub_dir = temp_path / "sub" / "dir"
            sub_dir.mkdir(parents=True)

            with patch("pathlib.Path.cwd", return_value=sub_dir):
                result = FrameworkPathResolver.find_framework_root()
                assert result == temp_path

    def test_find_framework_root_uvx_deployment(self):
        """Test finding framework root in UVX deployment scenario."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            claude_dir = temp_path / ".claude"
            claude_dir.mkdir()

            # Mock environment variable
            with patch.dict(os.environ, {"AMPLIHACK_ROOT": str(temp_path)}):
                with patch("pathlib.Path.cwd", return_value=Path("/unrelated/path")):
                    result = FrameworkPathResolver.find_framework_root()
                    assert result == temp_path

    def test_find_framework_root_not_found(self):
        """Test when framework root cannot be found."""
        with patch("pathlib.Path.cwd", return_value=Path("/")):
            with patch.dict(os.environ, {}, clear=True):
                result = FrameworkPathResolver.find_framework_root()
                assert result is None

    def test_resolve_framework_file_success(self):
        """Test successful framework file resolution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            claude_dir = temp_path / ".claude"
            claude_dir.mkdir()

            target_file = claude_dir / "test.md"
            target_file.write_text("test content")

            with patch("pathlib.Path.cwd", return_value=temp_path):
                result = FrameworkPathResolver.resolve_framework_file(".claude/test.md")
                assert result == target_file
                assert result is not None and result.exists()

    def test_resolve_framework_file_not_found(self):
        """Test framework file resolution when file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            claude_dir = temp_path / ".claude"
            claude_dir.mkdir()

            with patch("pathlib.Path.cwd", return_value=temp_path):
                result = FrameworkPathResolver.resolve_framework_file(".claude/nonexistent.md")
                assert result is None

    def test_resolve_framework_file_no_framework_root(self):
        """Test framework file resolution when framework root not found."""
        with patch("pathlib.Path.cwd", return_value=Path("/")):
            with patch.dict(os.environ, {}, clear=True):
                result = FrameworkPathResolver.resolve_framework_file(".claude/test.md")
                assert result is None
