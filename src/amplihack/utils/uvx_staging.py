"""UVX framework staging utilities."""

import os
import shutil
import sys
from pathlib import Path
from typing import Optional, Set


class UVXStager:
    """Handles staging of framework files from UVX to user's working directory."""

    def __init__(self):
        self._staged_files: Set[Path] = set()

    def detect_uvx_deployment(self) -> bool:
        """Detect if running in UVX deployment mode."""
        return "UV_PYTHON" in os.environ or not (Path.cwd() / ".claude").exists()

    def _find_uvx_framework_root(self) -> Optional[Path]:
        """Find framework root in UVX installation."""
        if "AMPLIHACK_ROOT" in os.environ:
            env_path = Path(os.environ["AMPLIHACK_ROOT"])
            if env_path.exists() and (env_path / ".claude").exists():
                return env_path

        for path_str in sys.path:
            candidate = Path(path_str) / "amplihack"
            if candidate.exists() and (candidate / ".claude").exists():
                return candidate

        return None

    def stage_framework_files(self) -> bool:
        """Stage framework files from UVX to working directory."""
        if not self.detect_uvx_deployment():
            return False

        uvx_root = self._find_uvx_framework_root()
        if not uvx_root:
            return False

        # Stage essential files only
        essential_files = [".claude/context", "CLAUDE.md"]
        working_dir = Path.cwd()

        for item_name in essential_files:
            source = uvx_root / item_name
            target = working_dir / item_name

            if not source.exists() or target.exists():
                continue

            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                if source.is_dir():
                    shutil.copytree(source, target, dirs_exist_ok=True)
                else:
                    shutil.copy2(source, target)
                self._staged_files.add(target)
            except Exception:
                pass  # Silent failure

        return len(self._staged_files) > 0


# Singleton instance for global use
_uvx_stager = UVXStager()


def stage_uvx_framework() -> bool:
    """Stage UVX framework files."""
    return _uvx_stager.stage_framework_files()


def is_uvx_deployment() -> bool:
    """Check if running in UVX deployment mode."""
    return _uvx_stager.detect_uvx_deployment()
