"""UVX framework staging utilities."""

import atexit
import os
import shutil
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Optional, Set


class UVXStager:
    """Handles staging of framework files from UVX to user's working directory."""

    def __init__(self):
        self._staged_files: Set[Path] = set()
        self._cleanup_registered = False

    def detect_uvx_deployment(self) -> bool:
        """Detect if running in UVX deployment mode.

        Returns:
            True if running via UVX, False for local deployment.
        """
        # Multiple indicators for UVX deployment
        uvx_indicators = [
            # Direct UVX environment variables
            "UV_PYTHON" in os.environ,
            "UVX_CACHE" in os.environ,
            # UV in Python path (UVX uses UV internally)
            any("uv" in path for path in sys.path),
            # No local .claude directory but framework files available elsewhere
            not (Path.cwd() / ".claude").exists() and self._find_uvx_framework_root() is not None,
        ]

        return any(uvx_indicators)

    def _find_uvx_framework_root(self) -> Optional[Path]:
        """Find framework root in UVX installation.

        Returns:
            Path to UVX framework root if found, None otherwise.
        """
        # Strategy 1: Environment variable (can be set by UVX wrapper)
        if "AMPLIHACK_ROOT" in os.environ:
            env_path = Path(os.environ["AMPLIHACK_ROOT"])
            if env_path.exists() and (env_path / ".claude").exists():
                return env_path

        # Strategy 2: Search Python path for amplihack installation
        for path_str in sys.path:
            path = Path(path_str)

            # Look for amplihack package directory
            amplihack_package = path / "amplihack"
            if amplihack_package.exists():
                # Check if framework files are included as package data
                framework_markers = [
                    amplihack_package / ".claude",
                    amplihack_package / "CLAUDE.md",
                ]

                if any(marker.exists() for marker in framework_markers):
                    return amplihack_package

            # Also check parent directories for traditional layout
            candidate = path.parent
            if candidate.exists():
                framework_markers = [
                    candidate / ".claude",
                    candidate / "CLAUDE.md",
                ]
                if any(marker.exists() for marker in framework_markers):
                    return candidate

        # Strategy 3: Check UVX cache directories
        cache_dirs = []

        # Common UVX cache locations
        if "UVX_CACHE" in os.environ:
            cache_dirs.append(Path(os.environ["UVX_CACHE"]))

        # Default cache locations by platform
        if os.name == "posix":
            home = Path.home()
            cache_dirs.extend(
                [
                    home / ".cache" / "uv",
                    home / ".local" / "share" / "uv",
                    Path("/tmp/uv-cache"),  # Temporary locations
                ]
            )
        elif os.name == "nt":
            cache_dirs.extend(
                [
                    Path(os.environ.get("LOCALAPPDATA", "")) / "uv",
                    Path(os.environ.get("APPDATA", "")) / "uv",
                ]
            )

        # Search cache directories for our repo
        for cache_dir in cache_dirs:
            if not cache_dir.exists():
                continue

            # Look for git clones with our framework files
            for repo_path in cache_dir.rglob("MicrosoftHackathon2025-AgenticCoding"):
                if (repo_path / ".claude").exists():
                    return repo_path

        # Strategy 4: Download from GitHub if in UVX environment
        if self.detect_uvx_deployment():
            return self._download_framework_files()

        return None

    def _download_framework_files(self) -> Optional[Path]:
        """Download framework files from GitHub to temporary location.

        Returns:
            Path to temporary directory with framework files, None on failure.
        """
        try:
            # Create temporary directory for downloaded files
            temp_dir = Path(tempfile.mkdtemp(prefix="amplihack_framework_"))

            # GitHub raw file base URL for the current branch
            # This should be updated to use the correct branch/commit
            base_url = "https://raw.githubusercontent.com/rysweet/MicrosoftHackathon2025-AgenticCoding/feat/issue-83-preference-uvx-fixes"

            # Essential files to download
            files_to_download = [
                "CLAUDE.md",
                "DISCOVERIES.md",
                ".claude/context/USER_PREFERENCES.md",
                ".claude/context/PHILOSOPHY.md",
                ".claude/context/PROJECT.md",
                ".claude/context/PATTERNS.md",
                ".claude/context/TRUST.md",
                ".claude/workflow/DEFAULT_WORKFLOW.md",
            ]

            success_count = 0
            for file_path in files_to_download:
                try:
                    file_url = f"{base_url}/{file_path}"
                    target_path = temp_dir / file_path

                    # Create parent directories
                    target_path.parent.mkdir(parents=True, exist_ok=True)

                    # Download file
                    urllib.request.urlretrieve(file_url, target_path)
                    success_count += 1

                except Exception as e:
                    print(f"Warning: Could not download {file_path}: {e}")

            if success_count > 0:
                return temp_dir

        except Exception as e:
            print(f"Error downloading framework files: {e}")

        return None

    def stage_framework_files(self) -> bool:
        """Stage framework files from UVX to working directory.

        Returns:
            True if staging successful, False otherwise.
        """
        if not self.detect_uvx_deployment():
            return False  # Not UVX deployment, nothing to stage

        uvx_root = self._find_uvx_framework_root()
        if not uvx_root:
            return False  # Can't find UVX framework files

        working_dir = Path.cwd()

        # Files/directories to stage for @ imports to work
        framework_items = [
            ".claude",
            "CLAUDE.md",
            "DISCOVERIES.md",  # Often referenced
        ]

        success = True
        staged_items = []

        for item_name in framework_items:
            source = uvx_root / item_name
            target = working_dir / item_name

            if not source.exists():
                continue  # Skip missing items

            if target.exists():
                continue  # Don't overwrite existing files

            try:
                if source.is_dir():
                    shutil.copytree(source, target)
                else:
                    shutil.copy2(source, target)

                self._staged_files.add(target)
                staged_items.append(item_name)

            except Exception as e:
                print(f"Warning: Could not stage {item_name}: {e}")
                success = False

        if staged_items and not self._cleanup_registered:
            # Register cleanup on exit
            atexit.register(self._cleanup_staged_files)
            self._cleanup_registered = True

        return success and len(staged_items) > 0

    def _cleanup_staged_files(self):
        """Clean up staged files on session end."""
        for staged_path in self._staged_files:
            try:
                if staged_path.exists():
                    if staged_path.is_dir():
                        shutil.rmtree(staged_path)
                    else:
                        staged_path.unlink()
            except Exception:
                pass  # Silent cleanup - don't break session end

        self._staged_files.clear()

    def cleanup_now(self):
        """Immediately clean up staged files."""
        self._cleanup_staged_files()

    def get_staged_files(self) -> Set[Path]:
        """Get list of currently staged files.

        Returns:
            Set of staged file paths.
        """
        return self._staged_files.copy()


# Singleton instance for global use
_uvx_stager = UVXStager()


def stage_uvx_framework() -> bool:
    """Convenience function to stage UVX framework files.

    Returns:
        True if staging successful or not needed, False on error.
    """
    return _uvx_stager.stage_framework_files()


def cleanup_uvx_staging():
    """Convenience function to clean up UVX staging."""
    _uvx_stager.cleanup_now()


def is_uvx_deployment() -> bool:
    """Check if running in UVX deployment mode.

    Returns:
        True if UVX deployment detected.
    """
    return _uvx_stager.detect_uvx_deployment()
