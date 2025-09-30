"""Simple file tracking registry for UVX cleanup operations.

Tracks files created during UVX staging for safe cleanup on exit.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set


@dataclass
class CleanupRegistry:
    """Tracks files to cleanup on exit.

    Simple file-based registry that records paths staged during
    UVX deployment for removal on exit.
    """

    session_id: str
    working_dir: Path
    _paths: Set[Path] = field(default_factory=set)

    def register(self, path: Path) -> bool:
        """Register a path for cleanup.

        Args:
            path: Path to track for cleanup

        Returns:
            True if path was registered, False if invalid
        """
        resolved = path.resolve()
        self._paths.add(resolved)
        return True

    def get_tracked_paths(self) -> List[Path]:
        """Get all tracked paths in deletion-safe order.

        Returns:
            List of paths, sorted deepest-first for safe deletion
        """
        # Sort by path depth (deepest first) for safe deletion
        return sorted(self._paths, key=lambda p: len(p.parts), reverse=True)

    def save(self, registry_path: Path | None = None) -> None:
        """Save registry to disk.

        Args:
            registry_path: Path to save registry (default: /tmp/amplihack-cleanup-{session_id}.json)
        """
        if registry_path is None:
            registry_path = Path(f"/tmp/amplihack-cleanup-{self.session_id}.json")

        data = {
            "session_id": self.session_id,
            "working_directory": str(self.working_dir),
            "paths": [str(p) for p in self._paths],
        }

        registry_path.write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, registry_path: Path) -> "CleanupRegistry | None":
        """Load registry from disk.

        Args:
            registry_path: Path to registry file

        Returns:
            CleanupRegistry if loaded successfully, None on error
        """
        try:
            data = json.loads(registry_path.read_text())
            registry = cls(
                session_id=data["session_id"], working_dir=Path(data["working_directory"])
            )
            registry._paths = {Path(p) for p in data["paths"]}
            return registry
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return None
