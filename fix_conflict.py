#!/usr/bin/env python3
"""Fix merge conflicts in stop.py by keeping pragma comment version.

Philosophy:
- Single responsibility: Only resolves pragma comment conflicts
- Standard library only: No external dependencies
- Explicit strategy: Clear selection logic with fallback
- Testable: Pure function design for easy testing

Public API (the "studs"):
    fix_conflict_content: Main conflict resolution function
    main: CLI entry point for standalone usage

Usage:
    python3 fix_conflict.py <file_path>

Returns:
    0 if conflict was fixed or no conflict found
    1 on error
"""

import sys
from pathlib import Path

__all__ = ["fix_conflict_content", "main"]


def fix_conflict_content(content: str) -> tuple[str, bool]:
    """Fix merge conflict by keeping the version with pragma comment.

    Strategy:
    1. Find conflict markers (<<<<<<, =======, >>>>>>>)
    2. Extract both versions (HEAD and theirs)
    3. Keep the version with pragma comment
    4. Fallback: keep longer line if neither has pragma
    5. Remove all conflict markers

    Args:
        content: File content with potential conflict markers

    Returns:
        Tuple of (fixed_content, was_conflict_found)
    """
    if "<<<<<<< HEAD" not in content:
        return content, False

    lines = content.splitlines(keepends=True)
    result = []
    i = 0
    conflict_found = False

    while i < len(lines):
        line = lines[i]

        # Found conflict start
        if line.strip().startswith("<<<<<<<"):
            conflict_found = True

            # Find the line between HEAD and =======
            i += 1
            head_line = lines[i]

            # Skip to =======
            while i < len(lines) and not lines[i].strip().startswith("======="):
                i += 1

            # Skip to >>>>>>> and grab their line
            i += 1
            their_line = lines[i]

            # Skip to end marker
            while i < len(lines) and not lines[i].strip().startswith(">>>>>>>"):
                i += 1

            # Robust selection: explicitly check for pragma comment
            if "pragma: allowlist secret" in head_line:
                result.append(head_line)
            elif "pragma: allowlist secret" in their_line:
                result.append(their_line)
            else:
                # Fallback: keep longer line (likely has more content)
                result.append(head_line if len(head_line) > len(their_line) else their_line)

            i += 1
        else:
            result.append(line)
            i += 1

    return "".join(result), conflict_found


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: fix_conflict.py <file_path>", file=sys.stderr)
        sys.exit(1)

    file_path = Path(sys.argv[1])

    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    try:
        content = file_path.read_text()
        fixed_content, conflict_found = fix_conflict_content(content)

        if conflict_found:
            file_path.write_text(fixed_content)
            print("Conflict resolved")
        else:
            print("No conflict found")

        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
